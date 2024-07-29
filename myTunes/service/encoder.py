from typing import Dict, Iterator

from music_tag import AudioFile, load_file

from service.converterTask import ConverterTask

__all__ = ('Settings', 'Encoder')


class Settings:
    guiSettings: Dict[str, Dict[str, any]]

    def stringify(self) -> str:
        """

        Returns: encoder settings as command args

        """
        self.verify()
        ...

    def verify(self) -> None:
        """
        check settings before apply them

        """
        ...

    def load(self, params: Dict[str, any]) -> None:
        """
        load new settings

        """
        for k,v in params.items():
            assert isinstance(self.__getattribute__(k), type(v)), TypeError(f'Not valid type for {k}')
            self.__setattr__(k, v)
        self.verify()

    def to_dict(self) -> Dict[str, any]:
        ...


class Encoder:
    name: str
    needWav: bool
    settings: Settings
    
    def _check(self) -> None:
        ...
    
    def verify_settings(self) -> None:
        self.settings.verify()

    def load_settings(self, settings: Dict[str, any]) -> None:
        self.settings.load(settings)

    def process_yield(self, fileIn: str, fileOut: str, settings: Dict[str, any] = None) -> Iterator[int]:
        """
        Convert audio files with ffmpeg encoder

        example call
         ffmpeg -i sample.mp3 -acodec pcm_s16le -ar 44100 sample.wav

         A large majority of audio files use little-endian encoding (pcm_s24le), not big (pcm_s24be)
         And most of them encoded as 16 bit (pcm_s16le)

        :param fileIn:
        :param fileOut:
        :param settings: custom settings
        :return: int: progress in % [0-100]
        """
        n = 0
        while n < 100:
            n += 1
            yield n
    
    def process(self, fileIn: str, fileOut: str) -> None:
        _ = [i for i in self.process_yield(fileIn, fileOut)]
        