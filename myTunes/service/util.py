import re
import os
from datetime import datetime
from typing import Iterable


def create_dirs(paths: Iterable[str]) -> None:
    for i in paths:
        if not os.path.exists(i):
            try:
                os.makedirs(i)
            except FileNotFoundError as e:
                raise FileNotFoundError(f'Fail to create dir {i}: {e}')
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