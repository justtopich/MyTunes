import configparser
import os
import pathlib
import re
import sys

import loguru
from loguru import logger as log

from myTunes.service.util import create_dirs


__all__ = ('cfg', 'log', 'KNOWN_FORMAT', 'LOSSLESS_FORMAT', 'ROOT_DIR')


LOSSLESS_FORMAT = set('wav,flac,aiff,ape'.split(','))
KNOWN_FORMAT = set('aac,m4a,mp3,ogg,mp4,wma,opus,m4r,mp2'.split(',')).union(LOSSLESS_FORMAT)
ROOT_DIR = pathlib.Path(__file__).parent.parent
sys.path.append(os.path.join(os.getcwd(), ".."))


# get version
def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


# config patch
class FakeMatch:
    def __init__(self, match):
        self.match = match

    def group(self, name):
        return self.match.group(name).lower()


class FakeRe:
    def __init__(self, regex):
        self.regex = regex

    def match(self, text):
        m = self.regex.match(text)
        if m:
            return FakeMatch(m)

        
def lowcase_sections(parser: configparser.RawConfigParser) -> configparser.RawConfigParser:
    parser.SECTCRE = FakeRe(re.compile(r"\[ *(?P<header>[^]]+?) *]"))
    return parser


# settings
class Library:
    rootPath: str
    syncPath: str


class Logger:
    level: str
    maxMb: int


class Settings:
    logger: Logger
    library: Library
    tempPath: str
    ffmpeg: str
    qaac: str

    def __init__(self, inifile: str):
        config = configparser.RawConfigParser(allow_no_value=True)
        config = lowcase_sections(config)
        
        try:
            config.read(inifile)
        except Exception as e:
            print(f"Fail to read configuration file: {e}")
            raise SystemExit(1)
        
        self.logger = Logger()
        self.logger.level = config.get('logger', 'level')
        self.logger.maxMb = config.getint('logger', 'max_mb')
        
        self.library = Library()
        self.library.rootPath = config.get('library', 'root_path')
        self.library.syncPath = config.get('library', 'sync_path')
        
        self.tempPath = config.get('converter', 'temp_path')
        self.ffmpeg = config.get('converter', 'ffmpeg')
        self.qaac = config.get('converter', 'qaac')
    

if __name__ != '__main__':
    cfg = Settings('settings.ini')
    
    cfg.logger.level = cfg.logger.level.upper()
    cfg.tempPath = os.path.normpath(cfg.tempPath)
    cfg.library.syncPath = os.path.normpath(cfg.library.syncPath)
    cfg.library.rootPath = os.path.normpath(cfg.library.rootPath.replace('\\', '/', -1))

    create_dirs(('tmp', 'logs',))

    # logging settings
    log.remove()
    if sys.stdout is not None:
        log.add(sys.stdout, level=cfg.logger.level, format='{time:YYYY-MM-DD HH:mm:ss} {level} {message}')
    log.add(
        f'{ROOT_DIR}/logs/MyTunes.log',
        level=cfg.logger.level,
        format='{time:YYYY-MM-DD HH:mm:ss} <level>{level: <8}</level>: {message}',
        rotation=f"{cfg.logger.maxMb} MB",
        compression="zip",
    )
