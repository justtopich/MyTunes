import os
import pathlib
import sys

import loguru
from loguru import logger as log

from pydantic import (
    AliasChoices,
    AmqpDsn,
    BaseModel,
    Field,
    ImportString,
    PostgresDsn,
    RedisDsn,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


__all__ = ('cfg', 'log', 'KNOWN_FORMAT', 'LOSSLESS_FORMAT', 'ROOT_DIR')


KNOWN_FORMAT = set('aac,m4a,mp3,ogg,wav,wave,flac,mp4,mpc,wma,aiff,ape'.split(','))
LOSSLESS_FORMAT = set('wav,wave,flac,aiff,ape'.split(','))
ROOT_DIR = pathlib.Path(__file__).parent.parent


def to_snake_case(string: str) -> str:
    if string.isupper():
        return string
    else:
        return (''.join(['_' + i.lower() if i.isupper() else i for i in string]).lstrip('_'))


class Library(BaseModel):
    rootPath: str
    
    class Config:
        alias_generator = to_snake_case


class Logger(BaseModel):
    level: str
    maxMb: int
    
    class Config:
        alias_generator = to_snake_case
        
        
class Settings(BaseSettings):
    logger: Logger
    library: Library
    syncPath: str
    tempPath: str
    ffmpeg: str
    qaac: str
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = '.'
        alias_generator = to_snake_case


cfg = Settings()

assert cfg.ffmpeg != "", ValueError("Empty ffmpeg parameter")
assert cfg.qaac != "", ValueError("Empty qaac parameter")
assert cfg.syncPath != "", ValueError("Empty syncPath parameter")
assert cfg.library.rootPath != "", ValueError("Empty library rootPath parameter")

cfg.logger.level = cfg.logger.level.upper()
cfg.tempPath = os.path.normpath(cfg.tempPath)
cfg.syncPath = os.path.normpath(cfg.syncPath)
cfg.library.rootPath = os.path.normpath(cfg.library.rootPath.replace('\\', '/', -1))

# logging settings
log.remove()
log.add(sys.stdout, level=cfg.logger.level, format='{time:YYYY-MM-DD HH:mm:ss} {level} {message}')
log.add(
    f'{ROOT_DIR}/logs/my_tunes.log',
    level=cfg.logger.level,
    format='{time:YYYY-MM-DD HH:mm:ss} <level>{level: <8}</level>: {message}',
    rotation=f"{cfg.logger.maxMb} MB",
    compression="zip"
)
