from typing import Union, Dict

__all__ = ('Settings', 'Encoder')


class Settings:
    def stringify(self) -> str:
        ...
    
    def load(self, params: Dict[str, any]) -> None:
        ...
    
    def to_dict(self) -> Dict[str, any]:
        ...


class Encoder:
    needWav: bool
    settings: Settings
    
    def _check(self) -> None:
        ...
    
    def validate_settings(self, settings: Dict[str, any]) -> None:
        self.settings.load(settings)
    
    def process(self, settings: Dict[str, any], fileIn: str, fileOut: Union[str, None] = None) -> str:
        """
        Convert audio files with ffmpeg encoder

        example call
         ffmpeg -i sample.mp3 -acodec pcm_s16le -ar 44100 sample.wav

         A large majority of audio files use little-endian encoding (pcm_s24le), not big (pcm_s24be)
         And most of them encoded as 16 bit (pcm_s16le)

        :param settings: encoder parameters
        :param fileIn:
        :param fileOut:
        :return: str: result file name
        """
        ...
