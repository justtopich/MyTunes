import os
from subprocess import Popen, PIPE, DEVNULL
from typing import Tuple, Dict

from my_tunes.config import log, cfg
from .encoder import Encoder, Settings


class SettingsQaac(Settings):
    """
        Attributes:
          bitrate. Default 320
          mode:
            - cbr bitrate [8-320] is default
            - abr bitrate [8-320]
            - cvbr bitrate [0-127] where 0 means best
            - tvbr bitrate [0-127]
          he: HE AAC mode (TVBR is not available)
          q: AAC encoding Quality [0-2] where 2 means best. Default 2
          rate: sample rate.
            - keep
            - auto
            - set in Hz
    """
    
    def __init__(self, bitrate=320, mode='cbr', he=False, frequency='auto', quality=2):
        self.bitrate = bitrate
        self.mode = mode
        self.he = he
        self.rate = frequency
        self.q = quality
    
    def stringify(self) -> str:
        if self.mode in ('abr', 'cbr', 'cvbr'):
            assert 8 <= self.bitrate <= 320, ValueError('Incorrect bitrate for this mode')
        elif self.mode == 'tvbr':
            assert 0 <= self.bitrate <= 127, ValueError('Incorrect bitrate for this mode')
        else:
            raise ValueError('unknown mode')
        
        assert 0 <= self.q <= 2, ValueError("Quality is incorrect")
        
        s = f"--{self.mode} {self.bitrate} --ignorelength -n --text-codepage 65001 -q {self.q} "
        
        if self.he:
            assert 0 < self.bitrate < 80, ValueError('Incorrect bitrate for this mode')
            assert self.mode != 'tvbr', ValueError('High Efficienc can be used with TVBR mode')
            s += "-- he "
        
        if self.rate not in ('keep', 'auto'):
            assert self.rate in ('8000', '11025', '12000', '16000', '22050', '24000', '32000', '44100',
                                 '48000'), ValueError("Incorrect sample rate value")
        
        s += f"--rate {self.rate}"
        return s


class Qaac(Encoder):
    def __init__(self):
        self.settings = SettingsQaac()
        self.needWav = True
        self.exe = cfg.qaac
        self._check()
    
    def _check(self):
        assert os.path.isfile(self.exe), ValueError(f'qaac exe file not exists')
        
        proc = Popen(
            '"{}" {}'.format(self.exe, "--check"),
            shell=True,
            encoding='cp866',
            stdout=PIPE,
            stderr=PIPE,
            stdin=DEVNULL,
        )
        stdout: [Tuple[bytes, bytes]] = proc.communicate()
        
        if stdout[0] != '' and stdout[1] != '':
            log.warning('qaac not respond')
        else:
            log.info(stdout[1])
    
    def process(self, settings: Dict[str, any], fileIn: str, fileOut: str = None) -> str:
        """
        Convert audio files with qaac encoder
        
        example qaac call
         qaac --cbr 320 --rate=44100 sweep96.wav -o cbr320.m4a
         
        :param settings:
        :param fileIn:
        :param fileOut:
        :return: str: result file name
        """
        # fileIn = fileIn.replace('/', '\\', -1)
        assert os.path.isfile(fileIn), FileNotFoundError(fileIn)
        
        if settings:
            self.validate_settings(settings)
        else:
            settings = self.settings
        
        if not fileOut:
            fileOut = f"{fileOut[:fileOut.rfind('.')]}.m4a"

        cmd = f'{self.exe} {settings.stringify()} "{fileIn}" -o "{fileOut}" '
        
        log.debug(cmd)
        
        proc = Popen(
            cmd,
            shell=True,
            encoding='cp866',
            stdout=PIPE,
            stderr=PIPE,
            stdin=DEVNULL,
        )
        stdout: [Tuple[bytes, bytes]] = proc.communicate()
        
        if stdout[0] != '' and stdout[1] != '':
            log.warning('qaac not respond')
        else:
            log.debug(f'qaac:\n{stdout[1]}')
        
        return fileOut
