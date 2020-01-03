from __future__ import unicode_literals
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError
from .config import *
from .logger import *
from .models import *
import os

logger = getLogger(__name__)

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
        'format': 'worst', # for debugging
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
                    results.append(parse(video_url, download))
            elif extractor == 'youtube:user':
                results.extend(parse(meta.get('url'), download))
            elif extractor == 'youtube':
                video = Video.initialize(meta)
                logger.info('Video: %s', video)

                if output_filename:
                    video.filename = output_filename
                    video.total_bytes = output_total_bytes
                    video.save()

                results.append(video)
            else:
                logger.warning('Unknown extractor: %s' % extractor)
    except DownloadError as e:
        logger.exception(e)
        logger.warning('Retry to parse URL: %s' % url)
        parse(url, download)

    return results
