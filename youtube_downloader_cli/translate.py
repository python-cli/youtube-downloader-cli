import logging
import googletrans
import requests
import time
import os
import json

from requests.exceptions import ProxyError, ConnectTimeout, ConnectionError
from .config import *

logger = logging.getLogger(__name__)

def translate2chinese(text, retry=10, cache=True):
    '''Translate the text to simplified chinese text.'''

    if not (text and len(text) > 0):
        return None

    result = None
    cached_dict = {}

    if os.path.exists(TRANSLATION_FILE):
        with open(TRANSLATION_FILE, 'r') as f:
            cached_dict = json.load(f)

    result = cached_dict.get(text)

    if result:
        return result

    translator = googletrans.Translator(proxies={
        'http': get_proxy(),
        'https': get_proxy(),
    }, timeout=60)

    try:
        logger.debug('translating [%s]', text)
        result = translator.translate(text, dest='zh-cn').text
    except (ProxyError, ConnectTimeout, ConnectionError) as e:
        logger.error('Connection error!')

        if retry >= 0:
            time.sleep(5)
            result = translate2chinese(text, retry=retry-1)
    except Exception as e:
        logger.exception(e)

    if cache and result and len(text) <= 100:
        cached_dict[text] = result

        with open(TRANSLATION_FILE, 'w') as f:
            json.dump(cached_dict, f, sort_keys=True, indent=4)

    return result
