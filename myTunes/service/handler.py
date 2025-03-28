import os
import shutil
import time
from queue import Queue
from typing import Dict, List

from PyQt6.QtCore import QThread, pyqtSignal, QMutex
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QProgressBar, QLabel, QListWidget, QListWidgetItem

from service.converter import Converter
from service.converterTask import ConverterTask
from myTunes.config import cfg, log, KNOWN_FORMAT, LOSSLESS_FORMAT
from service.util import create_dirs


class Hanlder(QThread):
    setProgress = pyqtSignal(tuple)
    
    def __init__(self, name: int, tasks: Queue[ConverterTask], progressName: QLabel,
                 logPage: QListWidget, converter: Converter, outPath: str, replaceOutFile: bool):
        super().__init__()
        self.colors = {
            'white': '#ffffff',
            'black': '#000000',
            'red': '#de5d70',
            'blue': '#badeff',
            'yellow': '#faef5a'
        }
        self.name = name
        self.tasks = tasks
        self.progressName = progressName
        self.logPage = logPage
        self.outPath = outPath
        self.replaceOutFile = replaceOutFile
        self.converter = converter
    
    def run(self):
        log.info(f"handler {self.name}: ready")

        while True:
            task: ConverterTask = self.tasks.get()
            if task == '--stop--':
                log.info(f"handler {self.name}: closed")
                self.tasks.task_done()
                break
            
            log.info(f'handler {self.name}: convert {task.afile.filename} -> {task.fileOut}')
            try:
                self.progressName.setText(f'{task.qTreePath}{task.baseName}')
                self.setProgress.emit((self.name, 0,))
                
                if not self.replaceOutFile and os.path.exists(f'{self.outPath}{task.fileOut}'):
                    log.info(f'handler {self.name}: exists {task.afile.filename}')
                    self.log_item(f'Exists: {task.fileOut}', 'blue')
                    self.setProgress.emit((self.name, 100,))
                    continue
                
                if self.outPath and not os.path.exists(f'{self.outPath}{task.qTreePath}'):
                    try:
                        create_dirs((f'{self.outPath}{task.qTreePath}',))
                    except Exception as e:
                        log.warning(f'handler {self.name}: create out dir: {e}')
                
                ext = task.baseName[task.baseName.rfind('.') + 1:].lower()
                if ext not in KNOWN_FORMAT:
                    # stat.unknownExt.add(ext)
                    continue
                
                if task.qTreePath:
                    try:
                        create_dirs((task.qTreePath,))
                    except Exception as e:
                        log.error(str(e))
                        continue
                
                isLossLess = False
                if ext == 'm4a' and self.converter.encoder.name == 'QAAC':
                    info = self.converter.ffmpeg.file_info(task.afile.filename)
                    if info['stream'].startswith('alac'):
                        isLossLess = True
                
                if isLossLess or ext in LOSSLESS_FORMAT:
                    task.fileOut = task.baseName
                    task.fileOut = f"{task.qTreePath}{task.fileOut[:task.fileOut.rfind('.')]}.{task.ext}"
                    
                    for i in self.converter.convert_afile(task.afile, f'{self.outPath}{task.fileOut}'):
                        self.setProgress.emit((self.name, i,))
                    
                    log.info(f'handler {self.name}: Done: {task.fileOut}')
                    self.log_item(f'Done: {task.fileOut}')
                else:
                    task.fileOut = f'{task.qTreePath}/{task.baseName}'
                    if not os.path.isfile(task.fileOut):
                        log.info(f'handler {self.name}: copy {task.afile.filename}')
                        shutil.copyfile(task.afile.filename, f'{self.outPath}{task.fileOut}')
                        self.log_item(f'Copy: {task.fileOut}')
                    else:
                        log.info(f'handler {self.name}: exists {task.afile.filename}')
                        self.log_item(f'Exists: {task.fileOut}', 'blue')

                self.setProgress.emit((self.name, 100,))
            except Exception as e:
                log.error(f"handler {self.name}: handler {self.name}: {e}")
                self.log_item(f'Error: {task.fileOut}: {e}', 'red')
            finally:
                self.tasks.task_done()
        
    def log_item(self, msg: str, color: str = 'transparent'):
        item = QListWidgetItem(msg)

        item.setBackground(QColor(self.colors.get(color, 'transparent')))
        self.logPage.insertItem(0, item)
