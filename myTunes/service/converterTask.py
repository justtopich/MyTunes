import os

from music_tag import AudioFile


class ConverterTask:
    def __init__(self, afile: AudioFile, qTreePath='', ext=''):
        if qTreePath != '':
            if qTreePath.startswith('/'):
                qTreePath = qTreePath[1:]
            if not qTreePath.endswith('/'):
                qTreePath += '/'
        
        self.afile = afile
        self.qTreePath = qTreePath
        self.baseName = os.path.basename(afile.filename)
        self.ext = ext
        self.fileOut = f'{self.qTreePath}{self.baseName[:self.baseName.rfind(".")]}.{ext}'
