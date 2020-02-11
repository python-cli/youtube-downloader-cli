#!/usr/bin/env python

import coloredlogs, logging, logging.config
from datetime import datetime
from functools import partial
import click
from youtube_downloader_cli.downloader import YTDownloader
from youtube_downloader_cli.models import setup_database
from youtube_downloader_cli.config import DATABASE_FILE

# Refer to
#   1. https://stackoverflow.com/a/7507842/1677041
#   2. https://stackoverflow.com/a/49400680/1677041
#   3. https://docs.python.org/2/library/logging.config.html
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'colored': {
            '()': 'coloredlogs.ColoredFormatter',
            'format': "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            'datefmt': '%H:%M:%S',
        }
    },
    'handlers': {
        'default': {
            'level': 'DEBUG' if __debug__ else 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'console': {
            'level': 'DEBUG' if __debug__ else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': 'main.log',
            'maxBytes': 1024 * 1024,
            'backupCount': 10
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'youtube_downloader_cli': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

click.option = partial(click.option, show_default=True)

@click.command()
@click.option('--download', '-d', default=False, type=click.BOOL,
              help='Whether download video or not.')
@click.argument('urls', type=click.STRING, nargs=-1)
def main(download, urls):
    """This tool is used to parse and download the youtube videos."""

    logger.info('Debug is %s', 'on' if __debug__ else 'off')
    setup_database(DATABASE_FILE)

    def filter_video(video):
        'Filter the uploaded date less than last 3 years.'
        upload_date = datetime.strptime(video.upload_date, '%Y%m%d')
        date_delta = upload_date - datetime.now()
        return date_delta.days <= 365 * 3

    for url in urls:
        downloader = YTDownloader(download=download, filter_func=filter_video)
        videos = downloader.parse(url)
        [logger.debug('Result: %s' % video) for video in videos]

if __name__ == '__main__':
    main()
