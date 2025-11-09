from PIL.ImageQt import QPixmap
from PyQt6.QtGui import QResizeEvent, QMouseEvent
from PyQt6.QtWidgets import QLabel, QFileDialog, QCheckBox, QComboBox

from PyQt6.QtCore import Qt

from myTunes.service.afileState import AfileState, Acover
from myTunes.service.util import ImageInfo
from config import log


class ImageLabel(QLabel):
    """
    Attributes:
        afileId: flag for file chooser
    """

    def __init__(self, afileState: AfileState, jpegNext: QCheckBox, quality: QComboBox):
        super(ImageLabel, self).__init__()
        with open('resource/music-disc.gif', 'rb') as f:
            self.defaultImg: bytes = f.read()

        self.jpegNext = jpegNext
        self.quality = quality

        self.img: bytes = self.defaultImg
        self.pixmap: QPixmap = QPixmap()
        self.afileState = afileState
        self.isDefault = True
        self.lastH: int = 1
        self.lastW: int = 1
        self.afilesId: str = None
        self.set_image()

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
            w = int(w0 / (h0 / h))
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

            acover: Acover = self.afileState.acovers[afileId]
            self.jpegNext.setChecked(acover.jpegNext)
            self.quality.setCurrentText(str(acover.quality))

        self.pixmap.loadFromData(self.img)
        self.setPixmap(self.pixmap)
        self.setMinimumSize(50, 50)
        self.setMaximumSize(500, 500)
        self.setLineWidth(3)
        self.lastH = 1
        self.lastW = 1
        self.scale_image()

        if not self.isDefault:
            info = ImageInfo(self.img)
            tooltip = f'{info.format}: {info.width}x{info.height}'
            self.jpegNext.setDisabled(False)
        else:
            tooltip = f'No image'
            self.jpegNext.setDisabled(True)

        self.setToolTip(tooltip)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.afileId is not None:
            file, _ = QFileDialog.getOpenFileName(self, 'Open File', './', "Image (*.png *.jpg *.jpeg *.webp)")
            if not file:
                return

            with open(file, 'rb') as f:
                self.set_image(f.read(), self.afileState.selectedAfilesId[0])

            for afileId in self.afileState.selectedAfilesId:
                log.debug('set image for afile %s: %s' % (afileId, file))
                self.afileState.acovers[afileId] = Acover(path=file)

            self.jpegNext.setChecked(True)
            self.jpegNext.setDisabled(False)
            self.quality.setCurrentText(str(Acover.quality))
