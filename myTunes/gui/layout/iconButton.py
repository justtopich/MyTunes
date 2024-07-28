from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtGui import QPixmap


class IconButton(QtWidgets.QPushButton):
    def __init__(self, *args, **kwargs):
        super(IconButton, self).__init__(*args, **kwargs)

    def setPixmap(self, pixmap: QPixmap):
        self.pixmap = pixmap

    def sizeHint(self):
        parent_size = QtWidgets.QPushButton.sizeHint(self)
        return QtCore.QSize(parent_size.width() + self.pixmap.width(), max(parent_size.height(), self.pixmap.height()))

    def paintEvent(self, event):
        QtWidgets.QPushButton.paintEvent(self, event)

        pos_x = 5  # hardcoded horizontal margin
        pos_y = int((self.height() - self.pixmap.height()) / 2)

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(pos_x, pos_y, self.pixmap)
