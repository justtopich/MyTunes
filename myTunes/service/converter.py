import os
import traceback
from queue import Queue
from threading import Thread
from typing import Dict, Iterator

from .encoder import Encoder
from .qaac import Qaac
from .ffmpeg import FFmpeg
from .converterTask import ConverterTask
from myTunes.config import cfg, log
from myTunes.service.tagEditor import TagEditor, AudioFile


class Converter:
    def __init__(self):
        try:
            self.qaac = Qaac()
        except Exception as e:
            log.error(f'load QAAC encoder: {e}')
        
        self.tagEditor = TagEditor()
        self.ffmpeg = FFmpeg()
        self.encoderName: Dict[str, Encoder] = {
            'QAAC': self.qaac,
            'FFmpeg': self.ffmpeg
        }
        self.queue: Queue[ConverterTask | str] = Queue()
        self.handlers: Dict[int, Thread] = {}
        # self.task: Dict[int, ibt=] = {}
        self.encoder: Encoder = self.ffmpeg
        self.outPath = ''
    
    def convert_afile(self, afile: AudioFile, fileOut: str) -> Iterator[int]:
        for i in self.convert_file(afile.filename, fileOut):
            yield i
        
        try:
            self.tagEditor.save_file(fileOut, afile)
        except Exception as e:
            msg = f'Set metadata for result file: {e}'
            log.error(msg)
            print(traceback.format_exc())
            raise RuntimeError(msg)
    
    def convert_file(self, fileIn: str, fileOut: str) -> Iterator[int]:
        """
        prepare file and call encoder
        
        :param fileIn:
        :param fileOut:
        :return: int: progress in % [0-100]
        """
        step1 = 0
        step2 = 0
        stepFactor = 1
        
        if self.encoder.needWav:
            # 30% reserved for this.
            tmpName = os.path.basename(fileIn)
            tmpName = f"{cfg.tempPath}/{tmpName[:tmpName.rfind('.')]}.wav"
            stepFactor = 0.7
            
            try:
                for i in self.ffmpeg.process_yield(fileIn, tmpName, {'-acodec': 'pcm_s16le'}):
                    step1 = int(i * 0.3)
                    yield step1
            except Exception as e:
                log.error(f'Create WAV: {e}')
                return False
        else:
            tmpName = fileIn
            
        try:
            for i in self.encoder.process_yield(tmpName, fileOut):
                step2 = int(i * stepFactor)
                yield step1 + step2
        except Exception as e:
            log.error(f'Encoder processing: {e}')
            raise Exception(f'Encoder processing: {e}')
        
        if self.encoder.needWav:
            try:
                os.remove(tmpName)
            except:
                pass
