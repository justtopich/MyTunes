import os.path
import time
from typing import Tuple, Dict, List

from PyQt6.QtCore import Qt
from music_tag import AudioFile
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QDialogButtonBox, QListWidget, QScrollBar, QApplication
from service.util import convert_to_jpeg, ImageInfo
from service.tagEditor import TAGS
from config import log
from myTunes.service.afileState import AfileState, Acover


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
        # group.addWidget(self.buttonStop)
        # layout.addLayout(group)
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


    def process_cover(self, afiles: List[AudioFile], treeView: 'MetadataLayout') -> None:
        self._process(afiles, treeView, coverMode=True)

    def process_meta(self, afiles: List[AudioFile], treeView: 'MetadataLayout') -> None:
        self._process(afiles, treeView, coverMode=False)

    def _process(self, afiles: List[AudioFile], treeView: 'MetadataLayout', coverMode=False) -> None:
        self.buttonStop.setEnabled(True)
        self.allDone = False
        self.stop = False
        self.logPage.clear()

        fewFiles = len(afiles) > 1
        for n, afile in enumerate(afiles):
            afileId = int(afile.qTreeViewRow[-1].text())
            if self.stop:
                break

            if not coverMode:
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
            else:
                acover =  self._afileState.acovers[int(afileId)]
                if acover.path:
                    with open(acover.path, mode='rb') as f:
                         afile['artwork'] = f.read()

                QApplication.processEvents()
                if acover.quality < 100:
                    log.info('convert to jpeg with quality %s' % (acover.quality))
                    afile['artwork'] = convert_to_jpeg(
                                afile['artwork'].first.data,
                                progressive=acover.jpegNext,
                                quality=acover.quality)

                acover.saved = True
                afile.qTreeViewRow[19].setText(ImageInfo(afile['artwork'].first.data).format)

            # if not self._treeView.tagsLayout.coverLayout.cover.isDefault:
                # afile['artwork'] = self._treeView.tagsLayout.coverLayout.cover.img

            QApplication.processEvents()
            filename = os.path.basename(afile.filename)

            try:
                afile.save()
            except Exception as e:
                log.error('save metadata %s: %s' % (filename, e))
                self.logPage.insertItem(0, f'error: {filename}')
            else:
                log.debug('save %s' % filename)
                self.logPage.insertItem(0, f'save: {filename}')

            self.progressBar.setValue(int(100/len(afiles)*n))
            QApplication.processEvents()
            time.sleep(.1)

        self.progressBar.setValue(100)
        self.allDone = True
        self.buttonStop.setEnabled(False)
