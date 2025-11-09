import sys
from typing import Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QGuiApplication
from PyQt6.QtWidgets import QApplication, QTreeView, QMainWindow, QVBoxLayout, QWidget, QSplitter, QGroupBox


class Tag:
    def __init__(self, name: str, title: str, multiTag=False):
        self.name = name
        self.title = title
        self.index = -1
        self.multiTag = multiTag


class MainWindow(QMainWindow):
    def __init__(self, treeview: QTreeView):
        super().__init__()
        screenSize = QGuiApplication.primaryScreen().geometry()
        height = screenSize.height()
        width = screenSize.width()

        self.setGeometry(int(width/4), int(height/4), int(width/2), int(height/2))
        self.setWindowTitle("MyTunes")
        # self.create_menu_bar()

        # workspace
        self.root = QVBoxLayout()
        self.main = QWidget()
        self.main.setLayout(self.root)
        self.setCentralWidget(self.main)
        self.main.setAcceptDrops(True)

        # divide workspace
        splitter = QSplitter(Qt.Orientation.Vertical)

        # # First group box
        group1 = QGroupBox()
        # group1 = FileBrowser()
        splitter.addWidget(group1)
        #
        # # Second group box
        self.treeView = treeview

        group2 = QGroupBox("Tracks")
        group2Box = QVBoxLayout()
        group2Box.addWidget(self.treeView)
        group2.setLayout(group2Box)
        splitter.addWidget(group2)

        self.root.addWidget(splitter)


def create_treeview() -> QTreeView:
    TAGS: Iterable[Tag] = (
        Tag('artist', 'Artist', True),
        Tag('tracktitle', 'Title'),
        Tag('album', 'Album', True),
        Tag('genre', 'Genre', True),
        Tag('year', 'Year', True),
        Tag('tracknumber', '#'),
        Tag('totaltracks', 'Total tracks', True),
        Tag('albumartist', 'Album artist', True),
        Tag('discnumber', '# Disc', True),
        Tag('totaldiscs', 'Total discs', True),
        Tag('composer', 'Composer', True),
        Tag('compilation', 'Compilation', True),
        Tag('lyrics', 'Lyrics'),
        Tag('isrc', 'isrc'),
        Tag('comment', 'Comment')
    )
    COLUMNS_HIDE = ('comment', 'lyrics', 'isrc', 'afileId')
    COLUMNS = ('Filename',) + tuple(i.title for i in TAGS if i.name not in COLUMNS_HIDE)
    COLUMNS_EXT = ('Bit rate', 'Sample rate', 'Format')

    view = QTreeView()
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Name", "Type", "Value"])

    # Example data
    rootParent = model.invisibleRootItem()

    for i in range(5):
        parent_item = QStandardItem(f"Item {i}")
        parent_item.appendRow([
            QStandardItem(f"Child {i}-0"),
            QStandardItem("Type A"),
            QStandardItem("Type A"*10),
            QStandardItem("Type A"*10),
            QStandardItem("Type A"*10),
            QStandardItem("Type A"*10),
            QStandardItem("Type A"),
            QStandardItem("Type A"),
            QStandardItem("Type A"),
            QStandardItem("123")
        ])
        rootParent.appendRow([parent_item, QStandardItem("Root Type"), QStandardItem("999")])

    model.setHorizontalHeaderLabels(COLUMNS + COLUMNS_EXT + COLUMNS_HIDE)
    view.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)  # <-- selects entire rows
    view.header().setDefaultSectionSize(80)
    view.setColumnWidth(0, 300)
    view.setAlternatingRowColors(True)
    view.setModel(model)

    for i in range(1, 4): view.setColumnWidth(i, 150)
    for i in range(5, 11): view.setColumnWidth(i, 40)
    for i in range(len(COLUMNS_HIDE)): view.hideColumn(len(COLUMNS + COLUMNS_EXT) + i)

    view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    view.setAcceptDrops(True)

    view.expandAll()
    return view


if __name__ == '__main__':
    guiApp = QApplication(sys.argv)
    guiApp.setStyle("fusion")
    guiApp.styleHints().setColorScheme(Qt.ColorScheme.Light)

    treeview = create_treeview()
    guiMainWindow = MainWindow(treeview)

    guiMainWindow.show()
    guiApp.exec()
