import os
from subprocess import Popen, PIPE, DEVNULL, check_output, STDOUT
from sys import stdout
from typing import Tuple, Dict, Iterator

from .encoder import Encoder, Settings
from myTunes.config import cfg, log


CODEC_FORMAT = {
    'aac': ('m4a', 'aac', 'mp4'),
    'libfdk_aac': ('m4a', 'aac', 'mp4'),
    'wavpack': ('wav',),
    'opus': ('ogg',),
}

ls = []
for i in CODEC_FORMAT.values():
    ls.extend(i)


class SettingsFF(Settings):
    def __init__(self, bitrate=320, mode='cbr', he=False, frequency='auto', quality=2):
        self.bitrate = bitrate
        self.mode = mode
        self.he = he
        self.rate = frequency
        self.q = quality
        self.codec = tuple(CODEC_FORMAT.keys())[0]
        self.format = CODEC_FORMAT[self.codec][0]
        self.guiSettings = {
            'Bitrate': {
                'value': ('320', '256', '192', '128', '64'),
                'attr': 'bitrate'},
            'Rate': {
                'value': (
                    'auto', 'keep', '8000', '11025', '12000', '16000', '22050', '24000', '32000', '44100', '48000'),
                'attr': 'rate'},
            'Codec': {
                'value': CODEC_FORMAT.keys(),
                'attr': 'codec'
            },
            'Format': {
                # 'value': CODEC_FORMAT[self.format],
                'value': set(ls),
                'attr': 'format'},
        }


class FFmpeg(Encoder):
    def __init__(self):
        self.name = 'FFmpeg'
        self.needWav = False
        self.exe = cfg.ffmpeg
        self.settings = SettingsFF()
        self._check()

    def _check(self):
        proc = Popen(
            f'"{self.exe}" -version',
            shell=True,
            encoding='cp866',
            stdout=PIPE,
            stderr=PIPE,
            stdin=DEVNULL,
        )
        stdout: [Tuple[bytes, bytes]] = proc.communicate()

        if stdout[0] != '' and stdout[1] != '':
            log.warning('ffmpeg not respond')
        else:
            if not stdout[0].startswith('ffmpeg version'):
                raise ValueError('Wrong ffmpeg version')
            lines = stdout[0].splitlines()

            log.info(lines[0])
            log.debug(stdout[0][len((lines[0])):])

    def file_info(self, file: str) -> Dict[str, str]:
        """
        get information about audio file
        
        :param file: path to file
        :return: attributes
        
        """
        info: Dict[str, str] = {}

        cmd = f'{self.exe} -i "{file}"'
        log.debug(cmd)

        proc = Popen(
            cmd,
            shell=True,
            encoding='cp866',
            stdout=PIPE,
            stderr=PIPE,
            stdin=DEVNULL)

        stdout: [Tuple[bytes, bytes]] = proc.communicate()

        if stdout[0] != '' and stdout[1] != '':
            log.warning('ffmpeg not respond')

        parseMeta = False
        lines = stdout[1].splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith('Metadata'):
                parseMeta = True
                continue
            elif line.startswith('Duration'):
                vals = line.split(', ')
                info['duration'] = vals[0][9:]
                info['start'] = vals[1][6:]
                info['bitrate'] = vals[2][8:]
                parseMeta = False
            elif line.startswith('Stream'):
                line = line[line.rfind('Audio') + 7:]
                vals = line.split(', ')
                info['stream'] = vals[0]
                info['rate'] = vals[1]
                info['channels'] = vals[2]
                info['depth'] = vals[3]
                break

            if parseMeta:
                idx = line.index(':')
                info[line[:idx].strip()] = line[idx + 1:].strip()

        return info

    def _parse_duration(self, s: str) -> int:
        s = s.split('.')[0]
        times = [int(i) for i in s.split(':')]
        dur = times[0] * 3600 + times[1] * 60 + times[2]
        return dur

    def process_yield(self, fileIn: str, fileOut: str, settings: Dict[str, any] = None) -> Iterator[int]:
        """
        Convert audio files with ffmpeg encoder

        example call
         ffmpeg -i sample.mp3 -acodec pcm_s16le -ar 44100 sample.wav
         
         A large majority of audio files use little-endian encoding (pcm_s24le), not big (pcm_s24be)
         And most of them encoded as 16 bit (pcm_s16le)

        converting to mp4 (m4a, mov etc) with cover in metadata can raise ffmpeg exception. For this used
        -disposition:v -attached_pic. See 8947 ticket
        
        :param fileIn:
        :param fileOut:
        :param settings: custom settings
        :return: int
        """

        # fileIn = fileIn.replace('/', '\\', -1)
        assert os.path.isfile(fileIn), FileNotFoundError(fileIn)
        
        if settings:
            paramsStr = ' '.join(' '.join((k, v)) for k, v in settings.items())
        else:
            paramsStr = ''
        
        duration = 0
        cmd = f'{self.exe} -i "{fileIn}"'
        with Popen(cmd, shell=True, encoding='cp866', stdout=PIPE, stderr=PIPE, stdin=DEVNULL) as proc:
            for line in proc.stderr:
                line = line.strip()
                if not line:
                    break
                elif line.startswith('Duration: '):
                    try:
                        duration = self._parse_duration(line[10:line.find('.')])
                    except Exception as e:
                        raise Exception(f'parse ffmpeg track duration [{line}]: {e}')
        
        assert duration > 0, f'file with zero duration: {fileIn}'
        
        duration2 = 0
        cmd = (f'{self.exe} -i "{fileIn}" -hide_banner -nostats -y -disposition:v -attached_pic -vn -progress - '
               f'{paramsStr} "{fileOut}"')
        log.debug(cmd)
        
        # stderr return info; stdout return progres
        error = ''

        with Popen(cmd, shell=False, encoding='cp866',
                   stdout=PIPE, stderr=STDOUT, stdin=DEVNULL,
                   universal_newlines=True,
                   ) as proc:

            while proc.poll() is None:
                done = 0

                for line in proc.stdout:
                    if line.startswith('out_time='):
                        duration2 = self._parse_duration(line[9:line.find('.')])
                    elif line.startswith('progress='):
                        if line.endswith('end'):
                            done = 100
                            break
                    elif 'Error' in line:
                        log.error(f'{line}')
                        error += f'\n{line}'

                    if done < 100 and duration:
                        done = int((100/duration) * duration2)

                    yield done

                if error:
                    log.error(f'ffmpeg: {error}')

                if not os.path.isfile(fileOut):
                    raise FileNotFoundError('No result file')
