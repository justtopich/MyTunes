import glob
import os
import shutil
from typing import Set

from my_tunes.config import version, cfg, log, KNOWN_FORMAT, LOSSLESS_FORMAT
from my_tunes.service.converter import Converter
from my_tunes.service.util import create_dirs


class Stat:
    def __init__(self):
        self.done = 0
        self.error = 0
        self.skip = 0
        self.converted = 0
        self.unknownExt:Set[str] = set()
    
    def print(self) -> str:
        return f"done: {self.done}\n" \
            f"error: {self.error}\n" \
            f"skip: {self.skip}\n" \
            f"converted: {self.converted}\n" \
            f"unknownExt: {','.join(self.unknownExt)}"


def convert_library():
    log.info(version)
    converter = Converter()
    stat = Stat()
    
    log.info(f'scan library {cfg.library.rootPath}')
    for file in glob.iglob(f'{cfg.library.rootPath}/**/*', recursive=True):
        if os.path.isfile(file):
            ext = file[file.rfind('.') + 1:].lower()
            if ext not in KNOWN_FORMAT:
                stat.unknownExt.add(ext)
                continue
            
            dirOut = os.path.dirname(file)
            dirOut = dirOut.replace(cfg.library.rootPath, cfg.library.syncPath)
            
            try:
                create_dirs((dirOut,))
            except Exception as e:
                log.error(str(e))
                break
            
            isLossLess = False
            if ext == 'm4a':
                info = converter.ffmpeg.file_info(file)
                if info['stream'].startswith('alac'):
                    isLossLess = True
            
            if isLossLess or ext in LOSSLESS_FORMAT:
                fileOut = os.path.basename(file)
                fileOut = f"{dirOut}/{fileOut[:fileOut.rfind('.')]}.m4a"
                
                if not os.path.isfile(fileOut):
                    log.info(f'convert {file} -> {fileOut}')
                    if converter.convert(converter.qaac, file, fileOut):
                        stat.done += 1
                    else:
                        stat.error += 1
                else:
                    stat.skip += 1
            
            else:
                fileOut = f'{dirOut}/{os.path.basename(file)}'
                if not os.path.isfile(fileOut):
                    log.info(f'copy {file}')
                    shutil.copyfile(file, fileOut)
                    stat.done += 1
                else:
                    stat.skip += 1
    
    log.info(f'Statistics:\n{stat.print()}')


if __name__ == '__main__':
    convert_library()
    