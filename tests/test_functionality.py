import sys
import os
import shutil
from typing import List, Set
import configparser
import pytest

import music_tag
from music_tag.file import AudioFile, MetadataItem, Artwork, TAG_MAP_ENTRY

from myTunes.service.util import create_dirs


TESTPATH = os.path.dirname(os.path.abspath(__file__))
CHANGES = os.path.join(TESTPATH, "..", "CHANGES.MD")
DATAPATH = (f'{TESTPATH}/in', f'{TESTPATH}/out',)
TESTFILE = 'neck.mp3'

sys.path.append(os.path.join(TESTPATH, ".."))

libraryFiles: List[str] = []
outFiles: List[str] = []


def setup():
    create_dirs(DATAPATH)
    
    print(f'\ncopy {TESTPATH}/../myTunes/settings.ini')
    config = configparser.ConfigParser()
    config.read(f'{TESTPATH}/../myTunes/settings.ini')
    config.set('converter', 'qaac', '..\myTunes\qaac\qaac64.exe')
    # config.set('logger', 'level', 'debug')
    
    with open(f'{TESTPATH}/settings.ini', 'w') as f:
        config.write(f)
    
    print(f'copy neck.mp3')
    shutil.copyfile(f'{TESTPATH}/{TESTFILE}', f'{TESTPATH}/in/{TESTFILE}')
    
    print('\nTest config')
    from myTunes.config import cfg
    
    cfg.library.rootPath = DATAPATH[0]
    cfg.library.syncPath = DATAPATH[1]


def teardown():
    print('\nteardown')
    os.remove(f'{TESTPATH}/settings.ini')
    
    for p in DATAPATH:
        shutil.rmtree(p)


@pytest.fixture(scope="session")
def configure():
    setup()
    yield
    teardown()

       
def test_ffmpeg():
    print('\nLoad ffmpeg')
    from myTunes.service.ffmpeg import FFmpeg
    ffmpeg = FFmpeg()
    assert isinstance(ffmpeg, FFmpeg), "Load FFmpeg encoder"
    
    print('Create music library')
    
    from myTunes.config import KNOWN_FORMAT
    
    fileIn = f'{DATAPATH[0]}/{TESTFILE}'
    testPaths = ('', '/мёд 玲/','/мёд 玲/22/')
    
    create_dirs([f'{DATAPATH[0]}{i}' for i in testPaths])
    
    n = 0
    for ext in KNOWN_FORMAT:
        if ext in ('m3u', 'ape', 'm4r'):
            continue
        
        if n == len(testPaths):
            n = 0
        
        fileOut = f'{DATAPATH[0]}/{testPaths[n]}{TESTFILE}-{ext}.{ext}'
        print(f'create {fileOut}')
        
        fileResult = ffmpeg.process(settings={}, fileIn=fileIn, fileOut=fileOut)
        assert fileResult == fileOut, "ffmpeg result file != file out parameter"
        libraryFiles.append(fileResult)
        
        n += 1


def test_converter_m4a():
    print()
    from myTunes.start import convert_library, LOSSLESS_FORMAT

    convert_library()

    for file in libraryFiles:
        outName = file.replace(DATAPATH[0], DATAPATH[1])

        if file.split('.')[-1] in LOSSLESS_FORMAT:
            outName = outName[:outName.rfind('.')] + '.m4a'

        assert os.path.isfile(outName), f"Not converted file {file}"
        outFiles.append(outName)

    print(f'\n convert files')
