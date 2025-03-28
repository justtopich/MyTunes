import os
from subprocess import Popen, PIPE, DEVNULL
from typing import Tuple, Dict, Iterator

from myTunes.config import log, cfg
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
        self.format = 'm4a'
        #TODO make class
        self.guiSettings = {
            'Mode': {
                'value': ('cbr', 'abr', 'cvbr', 'tvbr'),
                'attr': 'mode'},
            'Bitrate': {
                'value': ('320', '256', '192', '128', '64'),
                'attr': 'bitrate'},
            'Rate': {
                'value': (
                'auto', 'keep', '8000', '11025', '12000', '16000', '22050', '24000', '32000', '44100', '48000'),
                'attr': 'rate'},
            'Quality': {
                'value': ('2', '1', '0'),
                'attr': 'q'},
            'HE-AAC': {
                'value': False,
                'attr': 'he'},
            'Format': {
                'value': ('m4a', 'aac', 'mp4',),
                'attr': 'format'},
        }

    def stringify(self) -> str:
        self.verify()

        s = f"--{self.mode} {self.bitrate} --ignorelength -n --text-codepage 65001 -q {self.q} --rate {self.rate} "
        if self.he: s += "--he "
        return s

    def verify(self) -> None:
        if self.mode in ('abr', 'cbr', 'cvbr'):
            assert 8 <= self.bitrate <= 320, ValueError('Incorrect bitrate for this mode')
        elif self.mode == 'tvbr':
            assert 0 <= self.bitrate <= 127, ValueError('Incorrect bitrate for this mode')
        else:
            raise ValueError('unknown mode')

        assert 0 <= self.q <= 2, ValueError("Quality is incorrect")

        if self.he == True:
            assert 0 < self.bitrate < 80, ValueError('HE available for bitrate < 80')
            assert self.mode != 'tvbr', ValueError("HE can't be used with TVBR mode")

        if self.rate not in ('keep', 'auto'):
            assert self.rate in ('8000', '11025', '12000', '16000', '22050', '24000', '32000', '44100',
                                      '48000'), ValueError("Incorrect sample rate value")


class Qaac(Encoder):
    def __init__(self):
        self.name = 'QAAC'
        self.settings = SettingsQaac()
        self.needWav = True
        self.exe = cfg.qaac
        self._check()

    def _check(self):
        assert os.path.isfile(self.exe), ValueError(f'qaac exe file not exists')

        proc = Popen(
            '"{}" {}'.format(self.exe, "--check"),
            shell=True,
            encoding='utf-8',
            stdout=PIPE,
            stderr=PIPE,
            stdin=DEVNULL,
        )
        stdout: [Tuple[bytes, bytes]] = proc.communicate()

        if stdout[0] != '' and stdout[1] != '':
            log.warning('qaac not respond')
        else:
            log.info(stdout[1])

    def process_yield(self, fileIn: str, fileOut: str, settings: Dict[str, any] = None) -> Iterator[int]:
        """
        Convert audio files with qaac encoder
        
        example qaac call
         qaac --cbr 320 --rate=44100 sweep96.wav -o cbr320.m4a
         
        """
        assert os.path.isfile(fileIn), FileNotFoundError(fileIn)

        if not fileOut:
            fileOut = f"{fileOut[:fileOut.rfind('.')]}.{self.settings.format}"

        cmd = f'{self.exe} {self.settings.stringify()} "{fileIn}" -o "{fileOut}" '

        log.debug(cmd)

        proc = Popen(
            cmd,
            shell=True,
            encoding='cp866',
            stdout=PIPE,
            stderr=PIPE,
            stdin=DEVNULL,
        )
        
        done = 0
        while done < 100:
            line = ''
            for char in iter(lambda: proc.stderr.read(1), b""):
                if not char:
                    break
                elif char not in ('\r', '\n'):
                    line += char
                    continue

                # log.debug(line)
                if line.startswith('['):
                    done = int(float(line[1:line.find('%')]))
                    yield done
                
                line = ''
