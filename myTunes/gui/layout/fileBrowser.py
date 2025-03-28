from PyQt6.QtCore import QDir
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QGroupBox, QTreeView, QListView, QHBoxLayout, QSpacerItem, QSizePolicy


class FileBrowser(QGroupBox):
    def __init__(self):
        super(FileBrowser, self).__init__('Choose files')
        self.treeview = QTreeView()
        self.listview = QListView()
        # self.treeview.setHeaderHidden(True)
        # self.setAcceptDrops(True)

        self.setMinimumHeight(200)

        fileChooser = QHBoxLayout()
        fileChooser.addWidget(self.treeview, stretch=1)
        fileChooser.addSpacerItem(QSpacerItem(2, 2, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        fileChooser.addWidget(self.listview)

        self.dirModel = QFileSystemModel()
        self.dirModel.setRootPath('/')
        self.dirModel.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs)

        self.fileModel = QFileSystemModel()
        self.fileModel.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.Files | QDir.Filter.AllDirs)

        self.treeview.setDragEnabled(True)
        self.listview.setDragEnabled(True)
        self.treeview.setAnimated(True)
        self.treeview.setModel(self.dirModel)
        self.listview.setModel(self.fileModel)

        self.treeview.setRootIndex(self.fileModel.index(''))
        self.listview.setRootIndex(self.fileModel.index(QDir.rootPath()))
        self.listview.setMinimumWidth(self.width())

        self.treeview.setColumnWidth(0, 350)
        for i in range(1, self.dirModel.columnCount()):
            self.treeview.hideColumn(i)

        self.treeview.clicked.connect(self.on_clicked)

        self.setLayout(fileChooser)


    def on_clicked(self, index):
        path = self.dirModel.fileInfo(index).absoluteFilePath()
        self.listview.setRootIndex(self.fileModel.setRootPath(path))
