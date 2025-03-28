from typing import Iterable
import traceback
import re


import music_tag
from music_tag.file import AudioFile, MetadataItem, Artwork, TAG_MAP_ENTRY
from mutagen.mp4 import MP4Cover
from myTunes.config import log
from .util import parse_date

__all__ = ('Tag', 'TAGS', 'TagEditor', 'AudioFile')


class MetadataItemPatch(MetadataItem):
    """
    fix load file if int field is ''
    """
    
    @property
    def values(self):
        return self._values
    
    @values.setter
    def values(self, val):
        if isinstance(val, (list, tuple)):
            self._values = list(val)
        elif val is None:
            self._values = []
        else:
            self._values = [val]
        
        for i, v in enumerate(self._values):
            if self.type is int and isinstance(v, str):
                if not v:
                    log.warning(f'empty string in integer tag: {v}')
                    self._values[i] = None
                    continue
                    
                find = re.search(r'\D', v)
                if find:
                    log.warning(f'Not matched tag with integer type: {v}')
                    v = v[:find.start()]
            
            if self.sanitizer is not None:
                try:
                    v = self.sanitizer(v)
                except ValueError as e:
                    print(e)
                    v = None

            if not (self.type is None or v is None or isinstance(v, self.type) or v == ''):
                    v = self.type(v)
                    
            self._values[i] = v


class Tag:
    def __init__(self, name: str, title: str, multiTag=False):
        self.name = name
        self.title = title
        self.index = -1
        self.multiTag = multiTag


TAGS: Iterable[Tag] = (
    Tag('artist', 'Artist', True),
    Tag('tracktitle', 'Title'),
    Tag('album', 'Album', True),
    Tag('genre', 'Genre', True),
    Tag('year', 'Year', True),
    Tag('tracknumber', '#'),
    Tag('totaltracks', 'Total tracks', True),
    Tag('albumartist', 'Album artist', True),
    Tag('discnumber', '# Disc', True),
    Tag('totaldiscs', 'Total discs', True),
    Tag('composer', 'Composer', True),
    Tag('compilation', 'Compilation', True),
    Tag('lyrics', 'Lyrics'),
    Tag('isrc', 'isrc'),
    Tag('comment', 'Comment')
)


class TagEditor:
    def __init__(self):
        self._editor = music_tag
        self._patch_music_tag()
    
    def load_file(self, file: str) -> AudioFile:
        return self._editor.load_file(file)
    
    def save_file(self, file: str, metadata: AudioFile) -> None:
        afile: AudioFile = self._editor.load_file(file)
        
        for k in metadata.tag_map.keys():
            # print(f'{k}: {metadata[k].values}')
            
            if not k.startswith('#'):
                if k not in afile.tag_map:
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
                    afile[k] = value
                except ValueError as e:
                    if k == 'tracknumber':
                        for tag in metadata.mfile.tags:
                            if tag[0] == 'TRACKNUMBER':
                                if '/' in tag[1]:
                                    afile[k] = tag[1].split('/')[0]
                                else:
                                    raise ValueError(e)
                except Exception as e:
                    print(traceback.format_exc())
                    log.warning(f'not set metadata {k}: {e}')
        afile.save()
    
    def _set_artwork_patch(sef, afile: AudioFile, norm_key, artworks) -> None:
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
    
    def _get_artwork_patch(self, afile: AudioFile, norm_key) -> MetadataItem:
        if 'covr' not in afile.mfile.tags:
            artworks = []
        else:
            artworks = [Artwork(bytes(p)) for p in afile.mfile.tags['covr']]
        
        return MetadataItem(Artwork, None, artworks)
    
    def _patch_music_tag(self) -> None:
        self._editor.mp4.Mp4File._TAG_MAP['artwork'] = TAG_MAP_ENTRY(
            getter=self._get_artwork_patch, setter=self._set_artwork_patch, type=Artwork)
        
        self._editor.file.MetadataItem.values = MetadataItemPatch.values
