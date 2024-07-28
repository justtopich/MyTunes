from PyQt6.QtCore import QDir
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QGroupBox, QTreeView, QListView, QHBoxLayout, QSpacerItem, QSizePolicy


class FileBroser(QGroupBox):
    def __init__(self):
        super(FileBroser, self).__init__('Choose files')
        self.treeview = QTreeView()
        self.listview = QListView()
        # self.treeview.setHeaderHidden(True)
        # self.setAcceptDrops(True)

        self.setMinimumHeight(200)

        fileChooser = QHBoxLayout()
        fileChooser.addWidget(self.treeview, stretch=1)
        fileChooser.addSpacerItem(QSpacerItem(2, 2, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        fileChooser.addWidget(self.listview)

        path = QDir.rootPath()
        self.dirModel = QFileSystemModel()
        self.dirModel.setRootPath(path)
        self.dirModel.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs)

        self.fileModel = QFileSystemModel()
        self.fileModel.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.Files | QDir.Filter.AllDirs)

        self.treeview.setModel(self.dirModel)
        self.listview.setModel(self.fileModel)

        self.treeview.setRootIndex(self.dirModel.index(path))
        self.listview.setRootIndex(self.fileModel.index(path))
        self.listview.setDragEnabled(True)
        self.listview.setMinimumWidth(self.width())

        self.treeview.clicked.connect(self.on_clicked)

        self.setLayout(fileChooser)

    def on_clicked(self, index):
        path = self.dirModel.fileInfo(index).absoluteFilePath()
        self.listview.setRootIndex(self.fileModel.setRootPath(path))
