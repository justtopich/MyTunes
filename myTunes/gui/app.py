import sys
from os import abort
from typing import List, Dict

from PyQt6.QtCore import QDir, Qt
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from music_tag import AudioFile

from myTunes.service.converter import Converter
from myTunes.gui.layout import TagsLayout, MetadataLayout, CoverLayout, FileBrowser
from myTunes.gui.layout.treeView import TreeView
from myTunes.gui.layout.popup import InfoBox
from myTunes import __version__
from myTunes.service.afileState import AfileState


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
    def __init__(self, converter: Converter):
        super().__init__()
        screenSize = QGuiApplication.primaryScreen().geometry()
        height = screenSize.height()
        width = screenSize.width()
        self.afileState = AfileState()

        self.setGeometry(int(width/4), int(height/4), int(width/2), int(height/2))
        # self.setGeometry(50, 50, int(width / 1.4), int(height / 1.4))
        self.setWindowTitle("MyTunes")
        self.create_menu_bar()

        # workspace
        self.root = QVBoxLayout()
        self.main = QWidget()
        self.main.setLayout(self.root)
        self.setCentralWidget(self.main)
        self.main.setAcceptDrops(True)

        # divide workspace
        splitter = QSplitter(Qt.Orientation.Vertical)

        # First group box
        group1 = FileBrowser()
        splitter.addWidget(group1)

        # Second group box
        self.treeView = TreeView(self.afileState)

        group2 = QGroupBox("Tracks")
        group2Box = QVBoxLayout()
        group2Box.addWidget(self.treeView)
        group2.setLayout(group2Box)
        splitter.addWidget(group2)

        # Third group box
        self.settingsLayout: MetadataLayout = None
        self.coverLayout = CoverLayout(self.afileState)
        group3 = self.create_control(converter, self.treeView)
        self.treeView.tagsLayout = self.tags
        splitter.addWidget(group3)

        self.root.addWidget(splitter)

        with open('resource/icon.png', mode='rb') as f:
            icon = QPixmap()
            icon.loadFromData(f.read())
            self.setWindowIcon(QIcon(icon))

        self.aboutWidget = InfoBox(
            title='MyTunes about',
            message=f'MyTunes is open source audio converter and tags editor.\n\n'
                    f'Github: https://github.com/justtopich/MyTunes\n\n'
                    f'version: {__version__}')

    def create_menu_bar(self):
        menuBar = self.menuBar()
        editMenu = menuBar.addMenu("&Edit")
        self.settingsAction = QAction("&Settings", self)
        editMenu.addAction(self.settingsAction)
        self.settingsAction.triggered.connect(self.show_settings)

        helpMenu = menuBar.addMenu("&Help")
        self.aboutAction = QAction("&About", self)
        helpMenu.addAction(self.aboutAction)
        self.aboutAction.triggered.connect(self.show_about)

    def show_settings(self):
        from .layout.settingsWindow import SettingsWindow

        self.settingsWindow = SettingsWindow()
        self.settingsWindow.show()

    def show_about(self):
        self.aboutWidget.show()

    def create_control(self, converter: Converter, treeView: TreeView) -> QGroupBox:
        groupBox = QGroupBox('Metadata')
        control = QHBoxLayout()
        groupBox.adjustSize()
        # control.addStretch()

        control.addWidget(self.coverLayout)

        control.addWidget(createVerticalSeparator())
        self.tags = TagsLayout(treeView, self.coverLayout)

        control.addLayout(self.tags)
        control.addWidget(createVerticalSeparator())

        self.settingsLayout = MetadataLayout(converter, self.coverLayout, self.afileState)
        self.settingsLayout.set_treeView(self.treeView)
        control.addLayout(self.settingsLayout)

        self.treeView.tagsLayout =  self.tags
        groupBox.setLayout(control)

        return groupBox

    def resizeEvent(self, event):
        self.coverLayout.cover.scale_image()


def create_gui(converter: Converter) -> (QApplication, QMainWindow):
    guiApp = QApplication(sys.argv)
    guiApp.setStyle("fusion")
    guiApp.styleHints().setColorScheme(Qt.ColorScheme.Light)

    # if guiApp.styleHints().colorScheme().name == 'Dark':
    #     palette = QPalette()
    #     guiApp.setPalette(palette)

    guiMainWindow = MainWindow(converter)
    return guiApp, guiMainWindow
