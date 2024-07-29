import sys
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *


class WidgetMimeData(QtCore.QMimeData):
    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.itemObject = None

    def hasFormat(self, mime):
        if (self.itemObject and (mime == 'widgetitem')):
            return True
        return super().hasFormat(mime)

    def setItem(self, obj):
        self.itemObject = obj

    def item(self):
        return self.itemObject


class DraggableWidget(QGroupBox):
    def __init__(self):
        QWidget.__init__(self)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setAcceptDrops(True)

    def addWidget(self, widget):
        return self.layout().addWidget(widget)

    def mouseMoveEvent(self, ev):
        pixmap = QPixmap(self.size())
        # pixmap.fill(QtCore.Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setOpacity(0.8)
        painter.drawPixmap(0, 0, self.grab())
        painter.end()
        drag = QDrag(self)
        mimedata = WidgetMimeData()
        mimedata.setItem(self)
        drag.setMimeData(mimedata)
        drag.setPixmap(pixmap)
        drag.setHotSpot(ev.pos())
        drag.exec(QtCore.Qt.DropAction.MoveAction)

    def dragEnterEvent(self, ev):
        item = ev.mimeData().item()
        if item.isAncestorOf(self):
          #ev.ignore()
          ev.accept()
        else:
          ev.accept()

    def dropEvent(self, ev):
        # item = ev.mimeData().item()
        # if not item.isAncestorOf(self):
        #   print('dropped on', self.layout().itemAt(0).widget().text())
        ev.accept()


class HelloWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        w1 = DraggableWidget()
        w1.addWidget(QLabel('One'))
        w2 = DraggableWidget()
        w2.addWidget(QLabel('Two'))
        w3 = DraggableWidget()
        w3.addWidget(QLabel('Three'))
        w4 = DraggableWidget()
        w4.addWidget(QLabel('Four'))
        w5 = DraggableWidget()
        w5.addWidget(QLabel('Five'))

        w1.addWidget(w3)
        w1.addWidget(w4)
        w2.addWidget(w5)

        layout = QVBoxLayout()
        layout.addWidget(w1)
        layout.addWidget(w2)
        layout.addStretch(1)

        centralWidget = QWidget(self)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = HelloWindow()
    mainWin.show()
    sys.exit( app.exec())
