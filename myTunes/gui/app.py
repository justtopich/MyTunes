import sys

from PyQt6.QtCore import QDir, Qt
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from myTunes.service.converter import Converter
from myTunes.gui.layout import TagsLayout, SettingsLayout, ImageLabel, FileBroser
from myTunes.gui.layout.treeView import TreeView


__all__ = ('create_gui',)


class DraggableWidget(QGroupBox):
    def __init__(self):
        QWidget.__init__(self)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setAcceptDrops(True)

    def addWidget(self, widget):
        return self.layout().addWidget(widget)


def createVerticalSeparator() -> QFrame:
    result = QFrame()
    result.setFrameStyle(QFrame.Shape.VLine)
    return result


class MainWindow(QMainWindow):
    def create_file_chooser(self):
        groupBox = FileBroser()
        self.root.addWidget(groupBox)

    def create_control(self, converter: Converter, treeView: TreeView):
        groupBox = QGroupBox('Control')
        control = QHBoxLayout()

        self.cover = ImageLabel()
        control.addWidget(self.cover, Qt.AlignmentFlag.AlignLeft)

        control.addWidget(createVerticalSeparator())
        self.tags = TagsLayout(treeView, self.cover)

        control.addLayout(self.tags)
        control.addWidget(createVerticalSeparator())

        self.settingsLayout = SettingsLayout(converter)
        self.settingsLayout.set_treeView(self.treeView)
        control.addLayout(self.settingsLayout)

        groupBox.setLayout(control)
        self.root.addWidget(groupBox)
        self.treeView.tagsLayout =  self.tags

    def resizeEvent(self, event):
        self.tags.cover.scale_image()

    def __init__(self, converter: Converter):
        super().__init__()
        screenSize = QGuiApplication.primaryScreen().geometry()
        height = screenSize.height()
        width = screenSize.width()

        # self.setGeometry(int(width/4), int(height/4), int(width/2), int(height/2))
        self.setGeometry(50, 50, int(width/1.4), int(height/1.4))
        self.setWindowTitle("MyTunes")

        self.settingsLayout: SettingsLayout = None
        self.root = QVBoxLayout()
        self.create_file_chooser()
        self.root.addSpacerItem(QSpacerItem(2, 2, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.treeView = TreeView()
        self.root.addWidget(self.treeView)
        self.root.addSpacerItem(QSpacerItem(2, 2, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.create_control(converter, self.treeView)
        self.treeView.tagsLayout = self.tags
        self.root.addSpacerItem(QSpacerItem(2, 2, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.widget = QWidget()
        self.widget.setLayout(self.root)
        self.setCentralWidget(self.widget)
        self.widget.setAcceptDrops(True)
        with open('resource/icon.png', mode='rb') as f:
            icon = QPixmap()
            icon.loadFromData(f.read())
            self.setWindowIcon(QIcon(icon))

def create_gui(converter: Converter) -> (QApplication, QMainWindow):
    guiApp = QApplication(sys.argv)
    guiMainWindow = MainWindow(converter)
    return guiApp, guiMainWindow
