import logging
import googletrans
import requests
import time

from .config import get_proxy

logger = logging.getLogger(__name__)

def translate2chinese(text, retry=10):
    '''Translate the text to simplified chinese text.'''

    if not (text and len(text) > 0):
        return None

    translator = googletrans.Translator(proxies={
        'http': get_proxy(),
        'https': get_proxy(),
    }, timeout=60)

    result = None

    try:
        result = translator.translate(text, dest='zh-cn').text
    except requests.exceptions.ConnectTimeout as e:
        logger.exception(e)

        if retry >= 0:
            time.sleep(5)
            result = translate2chinese(text, retry=retry-1)
    except Exception as e:
        logger.exception(e)

    return result
