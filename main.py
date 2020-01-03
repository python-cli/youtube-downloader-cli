#!/usr/bin/env python

import click
from youtube_downloader_cli.downloader import parse
from youtube_downloader_cli.logger import *

logger = getLogger(__name__)

@click.command()
@click.option('--no-download', default=False, type=click.BOOL,
              help='Whether download video or not.')
@click.argument('urls', type=click.STRING, nargs=-1)
def main(no_download, urls):
    """This tool is used to parse and download the youtube videos."""

    for url in urls:
        videos = parse(url, not no_download)
        [logger.debug(video) for video in videos]

if __name__ == '__main__':
    main()
