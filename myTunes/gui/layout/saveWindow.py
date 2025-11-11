import os.path
import time
from typing import List, Generator, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QDialogButtonBox, QListWidget, QScrollBar, QApplication
from music_tag import AudioFile

from service.util import convert_to_jpeg, ImageInfo, get_afile_img
from service.afileState import AfileState, Acover
from service.tagEditor import TAGS
from config import log


class SaveWindow(QWidget):
    def __init__(self, afileState: AfileState):
        super().__init__()
        self.allDone = True
        self.stop = False
        self._afileState = afileState

        self.setWindowTitle('Saving')

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setMinimumWidth(400)
        self.setMinimumHeight(100)

        self.progressBar = QProgressBar()
        layout.addWidget(self.progressBar)

        self.buttonStop = QDialogButtonBox()
        self.buttonStop.addButton('Stop', QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttonStop.clicked.connect(self.break_process)
        layout.addWidget(self.buttonStop)

        self.logPage = QListWidget()
        self.logPage.setHorizontalScrollBar(QScrollBar(Qt.Orientation.Horizontal))
        self.logPage.setHorizontalScrollBar(QScrollBar(Qt.Orientation.Vertical))
        layout.addWidget(self.logPage)

    def create_window(self):
        self.progressBar.setValue(0)
        self.show()

    def close(self):
        if self.allDone:
            self.destroy()

    def break_process(self):
        self.buttonStop.setEnabled(False)
        self.stop = True
        msg = 'cancel by user'
        log.info(msg)
        self.logPage.insertItem(0, msg)

    def _process_cover(self, afiles: List[AudioFile], treeView: 'MetadataLayout') -> Generator[
        AudioFile, AudioFile, None]:
        acoverMaster: Acover = self._afileState.acovers[int(afiles[0].qTreeViewRow[-1].text())]

        if acoverMaster.path:
            with open(acoverMaster.path, mode='rb') as f:
                img = f.read()
            QApplication.processEvents()
        else:
            img = get_afile_img(afiles[0])

        if not img:
            return

        if acoverMaster.quality < 100:
            log.info('convert to jpeg with quality %s' % (acoverMaster.quality))
            img = convert_to_jpeg(img, progressive=acoverMaster.jpegNext, quality=acoverMaster.quality)
            QApplication.processEvents()

        for n, afile in enumerate(afiles):
            if self.stop:
                break

            afileId = int(afile.qTreeViewRow[-1].text())
            self._afileState.acovers[afileId].saved = True
            self._afileState.acovers[afileId].path = None
            afile['artwork'] = img
            afile.qTreeViewRow[19].setText(ImageInfo(afile['artwork'].first.data).format)
            yield afile

    def _process_meta(self, afiles: List[AudioFile], treeView: 'MetadataLayout') -> Generator[AudioFile, Any, None]:
        fewFiles = len(afiles) > 1
        for n, afile in enumerate(afiles):
            if self.stop:
                break

            for tag in TAGS:
                QApplication.processEvents()

                if fewFiles and not tag.multiTag:
                    continue

                val = treeView.tagsLayout.tags[tag.name].text()
                if val == '':
                    if tag.name in afile:
                        del afile[tag.name]
                else:
                    val = afile.get(tag.name).type(val)
                    afile[tag.name] = val

                afile.qTreeViewRow[tag.index].setText(str(val))

            yield afile

    def process(self, afiles: List[AudioFile], treeView: 'MetadataLayout', coverMode=False) -> None:
        self.buttonStop.setEnabled(True)
        self.allDone = False
        self.stop = False
        self.logPage.clear()

        if coverMode:
            processor = self._process_cover
        else:
            processor = self._process_meta

        for n, afile in enumerate(processor(afiles, treeView)):
            filename = os.path.basename(afile.filename)

            try:
                afile.save()
            except Exception as e:
                log.error('save metadata %s: %s' % (filename, e))
                self.logPage.insertItem(0, f'error: {filename}')
            else:
                log.debug('save %s' % filename)
                self.logPage.insertItem(0, f'save: {filename}')

            self.progressBar.setValue(int(100 / len(afiles) * n))
            QApplication.processEvents()
            time.sleep(.1)

        self.progressBar.setValue(100)
        self.allDone = True
        self.buttonStop.setEnabled(False)
