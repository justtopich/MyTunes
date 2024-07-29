import sys
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetDllDirectoryA(None)

from typing import Set

from config import log
from myTunes import __version__
from service.converter import Converter
from gui.app import create_gui


class Stat:
    def __init__(self):
        self.done = 0
        self.error = 0
        self.skip = 0
        self.converted = 0
        self.unknownExt: Set[str] = set()

    def print(self) -> str:
        return f"done: {self.done}\n" \
               f"error: {self.error}\n" \
               f"skip: {self.skip}\n" \
               f"converted: {self.converted}\n" \
               f"unknownExt: {','.join(self.unknownExt)}"


if __name__ == '__main__':
    log.info(f'MyTunes {__version__}')
    converter = Converter()
    stat = Stat()
    guiApp, guiMainWindow = create_gui(converter)
    guiMainWindow.show()
    guiApp.exec()
