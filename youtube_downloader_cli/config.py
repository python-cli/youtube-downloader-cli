from os import makedirs, remove
from os.path import join, exists, expanduser
import configparser
import json

_root = expanduser('~/.config/youtube-downloader-cli')
exists(_root) or makedirs(_root)

_config = None

CONFIG_FILE = join(_root, 'config')
DATABASE_FILE = join(_root, 'data.sqlite3')
TRANSLATION_FILE = join(_root, 'translation')

_SECTION_PROXY = 'PROXY'
_SECTION_STORAGE = 'STORAGE'

def _load_config():
    global _config

    if _config is None:
        _config = configparser.ConfigParser()

        if exists(CONFIG_FILE):
            _config.read(CONFIG_FILE)
        else:
            _config.add_section(_SECTION_PROXY)
            _config.set(_SECTION_PROXY, 'http', '')

            _config.add_section(_SECTION_STORAGE)
            _config.set(_SECTION_STORAGE, 'root_path', '~/Downloads/youtube-downloader-cli')

            with open(CONFIG_FILE, 'w') as f:
                _config.write(f)

    return _config

def pretty_json_string(dic):
    return json.dumps(dic, sort_keys=True, indent=4)

def get_raw_config():
    output = ''
    config = _load_config()

    for section in config.sections():
        output += '%s: \n' % section
        output += pretty_json_string(dict(config.items(section)))
        output += '\n\n'

    output += 'PATH: %s' % CONFIG_FILE

    return output

def get_proxy():
    return _load_config().get(_SECTION_PROXY, 'http')

def get_storage_path():
    config = _load_config()
    path = expanduser(config.get(_SECTION_STORAGE, 'root_path'))
    exists(path) or makedirs(path)
    return path
