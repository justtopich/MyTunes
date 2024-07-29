import time
from queue import Queue
from typing import List, Dict, Tuple

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QDialogButtonBox, QVBoxLayout, QLabel, \
    QListWidget, QProgressBar, QScrollBar, QScrollArea

from config import log
from service.converter import Converter
from service.converterTask import ConverterTask
from service.handler import Hanlder



class ProcessWindow(QWidget):
    def __init__(self, converter: Converter):
        super().__init__()
        self.setWindowTitle('Processing')
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)
        
        self.progressGroup = QVBoxLayout()
        scrollArea = QScrollArea()
        scrollArea.setHorizontalScrollBar(QScrollBar(Qt.Orientation.Horizontal))
        scrollArea.setLayout(self.progressGroup)
        layout.addWidget(scrollArea)
        
        # group = QHBoxLayout()
        self.logPage = QListWidget()
        self.logPage.setHorizontalScrollBar(QScrollBar(Qt.Orientation.Horizontal))
        self.logPage.setHorizontalScrollBar(QScrollBar(Qt.Orientation.Vertical))
        layout.addWidget(self.logPage)
        # layout.addLayout(group)
        
        group = QHBoxLayout()
        self.buttonClose = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.buttonClose.clicked.connect(self.close)
        group.addWidget(self.buttonClose)
        
        self.buttonStop = QDialogButtonBox()
        self.buttonStop.addButton('Stop', QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttonStop.clicked.connect(self.break_convert_files)
        group.addWidget(self.buttonStop)
        layout.addLayout(group)
        
        self.progressBar: Dict[int, QProgressBar] = {}
        self.progressName: Dict[int, QLabel] = {}
        self.threads = 4
        self.converter = converter
        self.queue: Queue[ConverterTask | str] = Queue()
        self.handlers: Dict[int, QThread] = {}
        self.progressBar: Dict[int, QProgressBar] = {}
        self.progressName: Dict[int, QLabel] = {}
        self.replaceOutfile = True
        self.allDone = True
    
    def break_convert_files(self):
        self.buttonStop.setEnabled(False)
        
        n = 0
        while n < len(self.handlers):
            task: str = self.queue.get()
            self.queue.task_done()
            if task == '--stop--':
                self.queue.put(task)
                n += 1
            else:
                log.info(f'cancel: {task.afile.filename}')
                self.logPage.insertItem(0, f'Cancel: {task.fileOut}')
        
    def close(self):
        if self.allDone:
            self.destroy()

    def set_progress(self, values: Tuple[int, int]):
        name, value = values
        self.progressBar[name].setValue(value)
    
    def create_window(self):
        self.logPage.clear()
        for i in self.progressBar.values(): i.deleteLater()
        for i in self.progressName.values(): i.deleteLater()
        self.progressBar.clear()
        self.progressName.clear()
        
        for i in range(self.threads):
            self.progressName[i] = QLabel('')
            self.progressGroup.addWidget(self.progressName[i])
            self.progressBar[i] = QProgressBar()
            self.progressBar[i].setRange(0, 100)
            self.progressBar[i].setMaximumHeight(int(self.height() * 0.04))
            # self.progressBar[i].setMinimumWidth(int(self.width()))
            self.progressBar[i].setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.progressGroup.addWidget(self.progressBar[i])
        self.show()
    
    def process(self, files: List[ConverterTask], outPath: str):
        assert self.queue.qsize() == 0, 'task queue is not empty'
        self.buttonStop.setEnabled(True)
        self.allDone = False
        
        if outPath and outPath[-1] not in ('/', '\\'):
            outPath += '/'
        
        for i in range(self.threads):
            th = Hanlder(i, self.queue, self.progressName[i], self.logPage, self.converter,
                         outPath, self.replaceOutfile)
            th.setProgress.connect(self.set_progress)
            self.handlers[i] = th
            th.start()
        
        for i in files:
            self.queue.put(i)
        
        for i in range(self.threads):
            self.queue.put('--stop--')
        
        while not self.queue.empty():
            time.sleep(1)
            
        self.queue.join()
        self.allDone = True
