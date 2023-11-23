import os
import traceback
from subprocess import Popen, PIPE, DEVNULL
from typing import Tuple, Iterable

import music_tag
from music_tag.file import AudioFile, MetadataItem, Artwork, TAG_MAP_ENTRY
from mutagen.mp4 import MP4Cover

from my_tunes.service.encoder import Encoder
from my_tunes.service.qaac import Qaac
from my_tunes.service.ffmpeg import FFmpeg
from my_tunes.service.util import parse_date
from my_tunes.config import cfg, log


def set_artwork_patch(afile, norm_key, artworks):
    if not isinstance(artworks, MetadataItem):
        raise TypeError()
    
    pics = []
    for art in artworks.values:
        if any(v is None for v in (art.mime,)):
            raise ImportError("Please install Pillow to properly handle images")
        
        mime_fmt = art.mime.split('/')[1].upper()
        if mime_fmt == 'JPEG':
            img_fmt = MP4Cover.FORMAT_JPEG
        elif mime_fmt == 'PNG':
            img_fmt = MP4Cover.FORMAT_PNG
        else:
            img_fmt = MP4Cover.FORMAT_JPEG
            log.warning('Unknown image type. May not saved artwork')
        
        pics.append(MP4Cover(art.raw, imageformat=img_fmt))
    afile.mfile.tags['covr'] = pics


def get_artwork_patch(afile, norm_key) -> MetadataItem:
    if 'covr' not in afile.mfile.tags:
        artworks = []
    else:
        artworks = [Artwork(bytes(p)) for p in afile.mfile.tags['covr']]
    
    return MetadataItem(Artwork, None, artworks)


# def filter_tag(tags: Iterable[Tuple[str, str]], tagName: str) -> bool:


class Converter:
    def __init__(self):
        self.patch_music_tag()
        self.ffmpeg = FFmpeg()
        
        try:
            self.qaac = Qaac()
        except Exception as e:
            log.error(f'load QAAC encoder: {e}')
    
    @staticmethod
    def patch_music_tag() -> None:
        music_tag.mp4.Mp4File._TAG_MAP['artwork'] = TAG_MAP_ENTRY(
            getter=get_artwork_patch, setter=set_artwork_patch, type=Artwork)
    
    def convert(self, encoder: Encoder, fileIn: str, fileOut: str = None) -> bool:
        """
        call encoder to process file
        :param encoder: encoder
        :param fileIn:
        :param fileOut:
        :return: bool: status
        """
        
        try:
            metadata:AudioFile = music_tag.load_file(fileIn)
        except Exception as e:
            log.error(f'Read metadata from {fileIn}')
            return False
        
        if encoder.needWav:
            outName = os.path.basename(fileIn)
            outName = f"{cfg.tempPath}/{outName[:outName.rfind('.')]}.wav"
            
            try:
                self.ffmpeg.process({'-acodec': 'pcm_s16le'}, fileIn, fileOut=outName)
            except Exception as e:
                log.error(f'Create WAV: {e}')
                return False
        else:
            outName = fileIn
        
        isDone = False
        
        try:
            encoder.process({}, outName, fileOut)
        except Exception as e:
            log.error(f'Encoder processing: {e}')
        else:
            isDone = True
        
        if encoder.needWav:
            try:
                os.remove(outName)
            except:
                pass
        
        try:
            metadataOut: AudioFile = music_tag.load_file(fileOut)
            for k in metadata.tag_map.keys():
                # print(f'{k}: {metadata[k].values}')
                
                if not k.startswith('#'):
                    if k not in metadataOut.tag_map:
                        log.warning(f"result file haven't metadata {k}")
                        continue
                    
                    if k == 'artwork':
                        if metadata[k].first is not None:
                            value: bytes = metadata[k].first.data
                        else:
                            continue
                    else:
                        try:
                            value = metadata[k]
                        except ValueError as e:
                            if k == 'year':
                                for tag in metadata.mfile.tags:
                                    if tag[0] == 'DATE':
                                        value = parse_date(tag[1]).strftime('%Y')
                            
                    try:
                        metadataOut[k] = value
                    except ValueError as e:
                        if k == 'tracknumber':
                            for tag in metadata.mfile.tags:
                                if tag[0] == 'TRACKNUMBER':
                                    if '/' in tag[1]:
                                        metadataOut[k] = tag[1].split('/')[0]
                                    else:
                                        raise ValueError(e)
                            
                    except Exception as e:
                        print(traceback.format_exc())
                        log.warning(f'not set metadata {k}: {e}')

            metadataOut.save()
        except Exception as e:
            log.error(f'Set metadata for result file: {e}')
            print(traceback.format_exc())
        
        return isDone
