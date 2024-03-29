from __future__ import unicode_literals
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError
from urllib.parse import urlparse
from fnmatch import fnmatch
from .config import get_storage_path, get_proxy
from .models import *
import os
import requests
import logging

logger = logging.getLogger(__name__)

class YTDownloader(object):
    'Youtube video downloader.'

    def __init__(self, download, filter_func=None):
        self.download = download
        self._filter_func = filter_func
        self._result_playlist = None
        self._result_videos = None

    @property
    def filter_func(self):
        return self._filter_func

    @property
    def result_playlist(self):
        return self._result_playlist

    @property
    def result_videos(self):
        return self._result_videos

    def parse(self, url, retry=10):
        'Parse the video url.'
        results = []

        output_filename, output_total_bytes = None, None

        def progress(d):
            if d['status'] != 'finished':
                return

            logger.info(f'Download completed with info: {d}')

            nonlocal output_filename, output_total_bytes
            head, tail = os.path.split(d.get('filename'))
            assert head == get_storage_path()
            output_filename = tail
            output_total_bytes = d.get('total_bytes')

        ydl_opts = {
            'format': 'worst' if __debug__ else 'best',
            'logger': logger,
            'progress_hooks': [progress],
            'proxy': get_proxy(),
            'forcejson': True,
            # 'verbose': True,
            # 'simulate': True,
            # 'skip_download': True,
            'extract_flat': True,
            'outtmpl': os.path.join(get_storage_path(), '%(title)s-%(id)s.%(ext)s'),
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                logger.info(f'Parsing url: {url}')
                meta = ydl.extract_info(url, download=self.download)
                extractor = meta.get('extractor')

                if extractor == 'youtube:playlist':
                    results.extend(self._parse_playlist(meta))
                elif extractor == 'youtube:tab':
                    results.extend(self._parse_tab(meta))
                elif extractor in ('youtube:channel', 'youtube:user'):
                    results.extend(self._parse_channel(meta))
                elif extractor == 'youtube':
                    video = self._parse_video(meta)

                    if video and output_filename:
                        video.filename = output_filename
                        video.total_bytes = output_total_bytes
                        video.save()

                    results.append(video)
                else:
                    logger.warning(f'Unknown extractor: {extractor}')
        except (requests.RequestException, DownloadError) as e:
            logger.exception(f'Encounter an exception [{e}] when parsing url [{url}], download option: {self.download}')

            if retry > 0:
                logger.warning(f'Retry to parse URL: {url}')
                results = self.parse(url, retry=retry-1)

        self._result_videos = results
        return results

    def _parse_playlist(self, meta):
        'Parse the playlist result.'
        logger.debug(f'Found playlist meta data: {meta}')

        results = []
        playlist = Playlist.initialize(meta)
        entries = meta.get('entries', [])
        count = len(entries)
        logger.info(f'Parse playlist: {playlist}, entry count: {count}')

        for i in range(count):
            entry = entries[i]
            video_id = entry.get('id')
            video_url = 'https://youtu.be/%s' % video_id

            logger.debug(f'Start parsing entry {i}:')
            videos = self.parse(video_url)
            assert len(videos) == 1
            video = videos[0]

            video.playlist = playlist
            video.save()
            results.append(video)

        logger.debug(f'Finish parsing playlist with {len(results)} video(s).')
        return results

    def _parse_tab(self, meta):
        'Parse the tab result.'
        logger.debug(f'Found tab meta data: {meta}')

        results = []
        playlist = Playlist.initialize(meta)
        entries = meta.get('entries', [])
        count = len(entries)
        logger.info(f'Parse tab playlist: {playlist}, entry count: {count}')

        for i in range(count):
            entry = entries[i]
            video_url = entry.get('url')

            logger.debug(f'Start parsing entry {i}:')
            videos = self.parse(video_url)

            for video in videos:
                video.playlist = playlist
                video.save()
                results.append(video)

        logger.debug(f'Finish parsing tab with {len(results)} video(s).')
        return results

    def _parse_channel(self, meta):
        'Parse the channel result.'
        logger.debug(f'Found channel meta data: {meta}')

        assert(meta.get('_type') == 'playlist')
        url = meta.get('url')
        logger.info(f'Parse channel list: {url}')
        return self.parse(url)

    def _parse_video(self, meta):
        'Parse the specified single video.'
        logger.debug(f'Found video meta data: {meta.get("url")}')

        video = Video.initialize(meta)
        valid = True

        if self.filter_func:
            valid = self.filter_func(video)

        if self.download and 'http' in video.thumbnail:
            _, filename = self._download_cover(video.thumbnail, video.id, 'jpg')
            video.thumbnail = filename
            video.save()

        if valid:
            logger.info(f'Found video: {video}')
            return video
        elif self.download:
            logger.info(f'Remove the downloaded files of invalid video: {video}')
            video.remove_cached_file()
        else:
            logger.info(f'Skipping video: {video}')

        return None

    def _download_cover(self, url, prefix, default_extension, retry=10):
        try:
            _, filename = os.path.split(urlparse(url).path)

            if '.' in filename:
                filename = '%s-%s' % (prefix, filename)
            else:
                filename = '%s-%s.%s' % (prefix, filename, default_extension)

            filepath = os.path.join(get_storage_path(), filename)

            if exists(filepath):
                logger.info('Found existing cover file "%s", reusing it...', filename)
                return filepath, filename

            logger.info('Downloading cover %s' % url)
            response = requests.get(url, proxies={
                'http': get_proxy(),
                'https': get_proxy(),
            })
            logger.info('Downloaded cover to %s' % filepath)

            with open(filepath, 'wb') as f:
                f.write(response.content)
        except (requests.RequestException, DownloadError) as e:
            if retry > 0:
                logger.warning('Retry to parse URL: %s' % url)
                filepath, filename = self._download_cover(url, prefix, default_extension, retry-1)
            else:
                logger.exception('Encounter an exception [%s] when downloading cover [%s]', e, url)
                filepath = None

        return filepath, filename

    @classmethod
    def cleanup(cls):
        'Clean up all the temporarily files generated by youtube-dl when downloading.'
        patterns = ['*.mp4.*']

        for root, dirs, files in os.walk(get_storage_path(), topdown=False):
            for name in files:
                if any(fnmatch(name, p) for p in patterns):
                    path = os.path.join(root, name)
                    logger.info('Removing file %s' % path)
                    os.remove(path)
