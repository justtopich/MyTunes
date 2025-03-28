from typing import Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QMouseEvent, QResizeEvent
from PyQt6.QtWidgets import QLabel, QLineEdit, QGridLayout, QFileDialog
from music_tag import Artwork
from mutagen.id3 import APIC

from gui.layout.popup import ErrorBox
from myTunes.service.tagEditor import AudioFile, TAGS, Tag
from myTunes.config import log


__all__ = ('TagsLayout','ImageLabel',)


class ImageLabel(QLabel):
    """
    Attributes:
        afileId: flag for file chooser
    """
    def __init__(self):
        super(ImageLabel, self).__init__()
        with open('resource/music-disc.gif', 'rb') as f:
            self.defaultImg: bytes = f.read()
        
        self.img: bytes = self.defaultImg
        self.pixmap: QPixmap = QPixmap()
        self.isDefault = True
        self.set_image()
        self.lastH: int = 1
        self.lastW: int = 1
        self.afilesId: str = None
        
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.scale_image()

    def scale_image(self) -> None:
        self.pixmap.loadFromData(self.img)
        h0 = self.pixmap.height()
        w0 = self.pixmap.width()
        h = self.height()
        w = self.width()
        
        # print(h,w)
        if h < w:
            w = int(w0/(h0/h))
        elif h > w:
            h = int(h0 / (w0 / w))
        
        if h > self.height():
            h = self.height()
            w = int(w0 / (h0 / h))
        elif w > self.width():
            w = self.width()
            h = int(h0 / (w0 / w))
        
        if self.lastH == h and self.lastW == w:
            return
        
        self.pixmap = self.pixmap.scaled(w, h, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.setPixmap(self.pixmap)
        self.lastH = h
        self.lastW = w

    def set_image(self, img: bytes = None, afileId: int = None) -> None:
        self.afileId = afileId
        if img is None:
            self.img = self.defaultImg
            self.isDefault = True
        else:
            self.img = img
            self.isDefault = False
        
        self.pixmap.loadFromData(self.img)
        self.setPixmap(self.pixmap)
        self.setMinimumSize(50, 50)
        self.setMaximumSize(500, 500)
        self.setLineWidth(3)
        self.lastH = 1
        self.lastW = 1
        self.scale_image()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.afileId is not None:
            file, _ = QFileDialog.getOpenFileName(self, 'Open File', './', "Image (*.png *.jpg *jpeg)")
            if file:
                with open(file, 'rb') as f:
                    self.set_image(f.read())


class TagsLayout(QGridLayout):
    def __init__(self, treeView: 'TreeView', imageLabel: ImageLabel):
        super(TagsLayout, self).__init__()
        self._treeView = treeView
        self.tags: Dict[str, QLineEdit] = {}
        self.cover = imageLabel
        colMax = 3 * 2 - 1

        row = 0
        col = 0
        for tag in TAGS:
            if col > colMax:
                row += 1
                col = 0

            self.tags[tag.name] = QLineEdit("")
            # print(f'{row}, {col}, {tag.name}')
            self.add_tag_line(row, col, tag)
            col += 2
        
        afileIdIdx = QLineEdit("")
        afileIdIdx.hide()
        self.addWidget(afileIdIdx, row, col + 1, )
        self.tags['afileId'] = afileIdIdx

    def add_tag_line(self, row: int, col: int, tag: Tag) -> None:
        self.addWidget(QLabel(f'{tag.title}:'), row, col, Qt.AlignmentFlag.AlignRight)
        # self.addWidget(getattr(self, name), index, 1+col)
        self.addWidget(self.tags[tag.name], row, col+1)

    def load_cover(self, afile: AudioFile, afileId: int) -> None:
        cover: bytes = self.cover.defaultImg

        try:
            apic: Artwork = afile['artwork'].first
            cover = apic.data
        except Exception as e:
            log.warning(f'load cover (1/2) for {afile.filename}: {e}')

        if cover is self.cover.defaultImg and 'APIC:' in afile.mfile.tags:
            try:
                apic: APIC = afile.mfile.tags['APIC:']
            except Exception as e:
                log.error(f'load cover (2/2) for {afile.filename}: {e}')
                ErrorBox(f"Can't load cover",
                         str(e)
                         ).exec()
            else:
                cover = apic.data

        self.cover.set_image(cover, afileId)

    def update_state(self, afiles: List[AudioFile] = None, afilesId: List[int] = None) -> None:
        if not afiles:
            self.tags['afileId'].setText('')
            self.cover.set_image()
            for tag in TAGS:
                self.tags[tag.name].setText('')
            return
        elif len(afiles) > 1:
            self.lock_tags()
        else:
            self.unlock_tags()
        
        afile = afiles[0]
        afileId = afilesId[0]
        self.tags['afileId'].setText(str(afileId))
        
        for tag in TAGS:
            val = afile[tag.name].first
            if val is None:
                self.tags[tag.name].setText('')
            else:
                self.tags[tag.name].setText(str(val))

        self.load_cover(afile, afileId)

    def lock_tags(self):
        for tag in TAGS:
            if not tag.multiTag:
                self.tags[tag.name].setEnabled(False)

    def unlock_tags(self):
        for tag in TAGS:
            self.tags[tag.name].setEnabled(True)
            