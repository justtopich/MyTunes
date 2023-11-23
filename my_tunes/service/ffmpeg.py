import os
from subprocess import Popen, PIPE, DEVNULL
from typing import Tuple, Dict

from .encoder import Encoder
from my_tunes.config import cfg, log


class FFmpeg(Encoder):
    def __init__(self):
        self.needWav = False
        self.exe = cfg.ffmpeg
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
            
            log.info(lines[0][:lines[0].find('-')])
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
    
    def process(self, settings: Dict[str, any], fileIn: str, fileOut: str = None) -> str:
        """
        Convert audio files with ffmpeg encoder

        example call
         ffmpeg -i sample.mp3 -acodec pcm_s16le -ar 44100 sample.wav
         
         A large majority of audio files use little-endian encoding (pcm_s24le), not big (pcm_s24be)
         And most of them encoded as 16 bit (pcm_s16le)

        converting to mp4 (m4a, mov etc) with cover in metadata can raise ffmpeg exception. For this used
        -disposition:v -attached_pic. See 8947 ticket
        
        
        :param settings:
        :param fileIn:
        :param fileOut:
        :return: str: result file name
        """
        
        # fileIn = fileIn.replace('/', '\\', -1)
        assert os.path.isfile(fileIn), FileNotFoundError(fileIn)
        
        paramsStr = ' '.join(' '.join((k, v)) for k, v in settings.items())
        
        cmd = f'{self.exe} -i "{fileIn}" -hide_banner -nostats -y -disposition:v -attached_pic {paramsStr} "{fileOut}" '
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
        
        if 'Output #0' in stdout[1]:
            log.debug(f'ffmpeg:\n{stdout[1]}')
        else:
            raise RuntimeError(f'ffmpeg:\n{stdout[1]}')
        
        if not os.path.isfile(fileOut):
            raise FileNotFoundError('No result file')
        
        return fileOut
