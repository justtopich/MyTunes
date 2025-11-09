from typing import List, Dict

from music_tag import AudioFile


class Acover:
    quality = 75

    def __init__(self, path: str=None, quality: int=100, jpegNext: bool=True):
        self.path= path
        self.quality = quality
        self.jpegNext = jpegNext
        self.saved = False


class AfileState:
    def __init__(self):
        self.selectedAfilesId: List[int] = []
        self.afiles: Dict[int, AudioFile] = {-1: None}
        self.acovers: Dict[int, Acover] = {-1: Acover()}
