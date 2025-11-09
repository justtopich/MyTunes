import re
import os
from datetime import datetime
from typing import Iterable
import io

from PIL import Image
from music_tag import AudioFile, Artwork


class ImageInfo:
    def __init__(self, img: bytes):
        imgPil = Image.open(io.BytesIO(img))
        self.format = imgPil.format
        self.height = imgPil.height
        self.width = imgPil.width


def get_afile_img(afile: AudioFile) -> bytes | None:
    img: bytes = None

    try:
        apic: Artwork = afile['artwork'].first
        img = apic.data
    except Exception as e:
        print(f'No artwork tag. Trying APIC for {afile.filename}: {e}')

    if not img and 'APIC:' in afile.mfile.tags:
        img = afile.mfile.tags['APIC:'].data

    return img


def convert_to_jpeg(
        cover: bytes,
        quality=75,
        progressive=False,
        rgb=True) -> bytes:
    """

    Args:
        cover: image
        progressive: use progressive JPEG
        quality: 0-100, 100 disables portions of the JPEG compression algorithm,
            and results in large files with hardly any gain in image quality
        rgb: keep RGB
    Returns:

    """
    image = Image.open(io.BytesIO(cover))
    image = image.convert('RGB')
    newImage = io.BytesIO()

    image.save(newImage, format='jpeg', quality=quality, keep_rgb=rgb, progressive=progressive)
    return newImage.getvalue()


def create_dirs(paths: Iterable[str]) -> None:
    exists = 0

    for i in paths:
        if not os.path.exists(i):
            try:
                os.makedirs(i)
            except FileNotFoundError as e:
                raise FileNotFoundError(f'Fail to create dir {i}: {e}')
            except FileExistsError:
                exists += 1
            except Exception as e:
                raise Exception(f'Fail to create dir {i}: {e}')


def parse_date(string: str) -> datetime:
    sDate = ''
    sTime = ''
    timeFormat = ''
    dateFormat = '%d/%m/%Y'
    
    string = string.replace('T', ' ', -1)
    idx = string.rfind(' ')
    if idx != -1:
        sDate = string[:idx + 1]
        sTime = string[idx:]
        
        if ':' in sTime:
            timeFormat += " %H:%M:%S"
    else:
        sDate = string
    

    if re.match(r'\d\d\d\d', sDate):
        dateFormat = '%Y'
    if re.match(r'^\d\d\d\d', sDate):
        dateFormat = "%Y/%m/%d"
    elif re.match(r'.*\d\d\d\d', sDate):
        dateFormat = "%m/%d/%Y"
    
    if re.match(r'.*[a-zA-Z].*', sDate):
        dateFormat = dateFormat.replace('%m', '%B')
    
    if '.' in sDate:
        dateFormat = dateFormat.replace('/', '.', -1)
    if '-' in sDate:
        dateFormat = dateFormat.replace('/', '-', -1)
    if ' ' in sDate:
        dateFormat = dateFormat.replace('/', ' ', -1)
    
    mask = f'{dateFormat}{timeFormat}'
    # print(mask)
    
    while True:
        try:
            dt = datetime.strptime(string, mask)
        except ValueError as e:
            if '%B' in mask:
                mask = mask.replace('%B', '%b')
            else:
                raise ValueError(e)
            
        except Exception as e:
            raise Exception(e)
        else:
            break
    
    return dt

# parse_date('2005 March 08')
# parse_date('19-10-04')
# parse_date('2013.12.30')
# parse_date('Jan-02-2010')