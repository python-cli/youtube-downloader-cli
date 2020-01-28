from __future__ import unicode_literals
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError
from urllib.parse import urlparse
from .config import *
from .logger import *
from .models import *
import os
import requests

logger = getLogger(__name__)

def download_cover(url, output_dir, prefix, default_extension):
    try:
        _, filename = os.path.split(urlparse(url).path)

        if '.' in filename:
            filename = '%s-%s' % (prefix, filename)
        else:
            filename = '%s-%s.%s' % (prefix, filename, default_extension)

        filepath = os.path.join(output_dir, filename)

        if exists(filepath):
            logger.info('Found existing file here, reusing it...')
            return filepath, filename

        logger.info('Downloading %s' % url)
        response = requests.get(url, proxies={
            'http': get_proxy(),
            'https': get_proxy(),
            })
        logger.info('Downloaded to %s' % filepath)

        with open(filepath, 'wb') as f:
            f.write(response.content)
    except requests.RequestException as e:
        logger.exception(e)
        filepath = None

    return filepath, filename

def parse(url, download=False):
    results = []

    output_filename, output_total_bytes = None, None

    def progress(d):
        if d['status'] == 'finished':
            logger.info('Download completed with info: %s' % d)

            nonlocal output_filename, output_total_bytes
            head, tail = os.path.split(d.get('filename'))
            assert head == get_storage_path()
            output_filename = tail
            output_total_bytes = d.get('total_bytes')

    ydl_opts = {
        # 'format': 'worst', # for debugging
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
            # ydl.download([url])
            meta = ydl.extract_info(url, download=download)
            extractor = meta.get('extractor')

            if extractor == 'youtube:playlist':
                playlist = Playlist.initialize(meta)
                logger.info('Playlist: %s', playlist)

                for entry in meta.get('entries'):
                    video_id = entry.get('id')
                    video_url = 'https://youtu.be/%s' % video_id

                    for video in parse(video_url, download):
                        video.playlist = playlist
                        video.save()
                        results.append(video)
            elif extractor == 'youtube:user':
                videos = parse(meta.get('url'), download)
                results.extend(videos)
            elif extractor == 'youtube':
                video = Video.initialize(meta)
                logger.info('Video: %s', video)

                if output_filename:
                    video.filename = output_filename
                    video.total_bytes = output_total_bytes
                    video.save()

                if 'http' in video.thumbnail:
                    _, filename = download_cover(video.thumbnail, get_storage_path(), video.id, 'jpg')
                    video.thumbnail = filename
                    video.save()

                results.append(video)
            else:
                logger.warning('Unknown extractor: %s' % extractor)
    except DownloadError as e:
        logger.exception(e)
        logger.warning('Retry to parse URL: %s' % url)

        results = parse(url, download)

    return results
