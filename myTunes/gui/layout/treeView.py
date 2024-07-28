import glob
import os
import traceback
from functools import partial
from typing import Dict, List, Tuple

from PyQt6.QtCore import QItemSelectionModel, Qt, QPoint, QItemSelection, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QDropEvent, QDragMoveEvent, QDragEnterEvent
from PyQt6.QtWidgets import QTreeView,  QMenu, QAbstractItemView
from music_tag.file import TAG_MAP_ENTRY

from config import log, cfg, KNOWN_FORMAT
from service.tagEditor import TagEditor, AudioFile, TAGS, Tag
from .popup import ErrorBox
from .tagsLayout import TagsLayout

COLUMNS_HIDE = ('comment', 'lyrics', 'isrc', 'afileId')
COLUMNS = ('Filename',) + tuple(i.title for i in TAGS if i.name not in COLUMNS_HIDE)
COLUMNS_EXT =  ('Bit rate', 'Sample rate', 'Format')


class TreeView(QTreeView):
    """
     Attributes:
         parent: root QStandardItem for files
         afiles: links to afile
         afileTree: afile metadata in treeview
    """
    def __init__(self):
        super().__init__()
        self.tagsLayout: TagsLayout = None
        self.selectedAfilesId: List[int] = []
        
        self.modelRow = QStandardItemModel()
        self.modelRow.setHorizontalHeaderLabels(COLUMNS + COLUMNS_EXT + COLUMNS_HIDE)
        self.setModel(self.modelRow)
        self.header().setDefaultSectionSize(80)
        self.setColumnWidth(0, 300)
        self.setAlternatingRowColors(True)
        
        for i in range(1, 4): self.setColumnWidth(i, 150)
        for i in range(5,11): self.setColumnWidth(i, 40)
        
        self.headerTag: Dict[int, Tag] = {}
        self._set_tag_index()
        for i in range(len(COLUMNS_HIDE)): self.hideColumn(len(COLUMNS + COLUMNS_EXT) + i)
        
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        
        self.rootParent = self.modelRow.invisibleRootItem()
        self.tagEditor = TagEditor()
        self.afiles: Dict[int, AudioFile] = {-1: None}
        # self.afileTree: Dict[int, QStandardItem] = {-1: None}
        
    def _set_tag_index(self):
        for n, col in enumerate(COLUMNS + COLUMNS_EXT + COLUMNS_HIDE):
            for tag in TAGS:
                if tag.title == col or tag.name == col:
                    tag.index = n
                    self.headerTag[n] = tag
                    break

    def _get_selected_rows(self) -> List[Tuple[QModelIndex, ...]]:
        rows: List[Tuple[QModelIndex, ...]] = []
        values: List[QModelIndex] = []
        rowIdx = -1
        
        selectionModel: QItemSelectionModel = self.selectionModel()
        for i in selectionModel.selectedIndexes():
            item = self.modelRow.itemFromIndex(i)
            if i.row() != rowIdx:
                if values:
                    rows.append(tuple(values))
                rowIdx = i.row()
                values.clear()
            values.append(i)
        
        if values:
            rows.append(tuple(values))
        return rows

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        # print('--new select--')
        self.selectedAfilesId.clear()
        
        rows = self._get_selected_rows()
        if not rows:
            if self.tagsLayout is not None:
                self.tagsLayout.update_state()
            return
        
        afiles: List[AudioFile] = []
        selectedAfilesId: List[int] = []
        for row in rows:
            # print(f"select: {row[0].data()}")
            
            # root item always have max columns
            if len(row) > 1 and row[-1].data() is not None:
                aFileId = row[-1].data()
                if int(aFileId) in self.afiles:
                    aFileId = int(aFileId)
                    afiles.append(self.afiles[aFileId])
                    selectedAfilesId.append(aFileId)
        
        self.selectedAfilesId = selectedAfilesId
        self.tagsLayout.update_state(afiles, selectedAfilesId)
                
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def _make_row(self, file: str) -> List[QStandardItem]:
        row: List[QStandardItem] = [QStandardItem(os.path.basename(file))]

        try:
            metadata: AudioFile = self.tagEditor.load_file(file)
        except Exception as e:
            print(traceback.format_exc())
            msg = f'load file tags: {file}: {e}'
            log.error(msg)
            raise Exception(msg)

        for n in range(1, self.header().model().columnCount()-1):
            tag = self.headerTag.get(n)
            if tag is None:
                row.append(QStandardItem(tag))
            else:
                try:
                    val = metadata[tag.name].first
                    if val is None: val = ''
                    row.append(QStandardItem(str(val)))
                except Exception as e:
                    print(traceback.format_exc())
                    raise Exception(f'{file}: load tag {tag.title}: {e}')

        afileId = max(self.afiles.keys()) + 1
        row.append(QStandardItem(str(afileId)))
        
        metadata.qTreeViewRow = row
        self.afiles[afileId] = metadata
        # self.afileTree[afileId] = row
        return row
    
    def pass_file(self, uFile: str) -> bool:
        ext = uFile[uFile.rfind('.') + 1:].lower()
        return ext in KNOWN_FORMAT

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

            parents: Dict[str, QStandardItem] = {}
            try:
                for url in event.mimeData().urls():
                    if url.isLocalFile():
                        uFile = url.toLocalFile()
                        parent = self.rootParent
                        
                        if os.path.isfile(uFile):
                            if self.pass_file(uFile):
                                log.debug(f'add root file {uFile}')
                                parent.appendRow(self._make_row(uFile))
                        else:
                            log.debug(f'add root path {uFile}')
                            parent.appendRow((
                                QStandardItem(os.path.basename(uFile))
                            ))
                            parents[uFile] = parent.child(parent.rowCount() - 1)
    
                            for uFile in glob.iglob(f'{url.toLocalFile()}/**/*', recursive=True):
                                if uFile.startswith(cfg.library.syncPath):
                                    continue
                                
                                if os.path.isfile(uFile):
                                    if not self.pass_file(uFile):
                                        continue
                                    
                                    log.debug(f'add file {uFile}')
                                    parents[os.path.dirname(uFile)].appendRow(self._make_row(uFile))
                                    # print(uFile, os.path.dirname(uFile))
                                    # print('parent', parents[os.path.dirname(uFile)])
                                    # print('idx', parents[os.path.dirname(uFile)].rowCount() -1)
                                else:
                                    newParent = QStandardItem(os.path.basename(uFile))
                                    parents[os.path.dirname(uFile)].appendRow(newParent)
                                    parents[uFile] = newParent
                                    
                                    log.debug(f'add path {newParent.text()}')
                                    
                    for i in parents.values():
                        self.setExpanded(i.index(), True)
            except Exception as e:
                ErrorBox(
                    'Import error',
                    str(e)
                ).exec()
        else:
            event.ignore()

    def open_menu(self, position: QPoint) -> None:
        # indexes = self.sender().selectedIndexes()
        mdlIdx = self.indexAt(position)

        if not mdlIdx.isValid():
            return

        item = self.modelRow.itemFromIndex(mdlIdx)
        # if len(indexes) > 0:
        #     level = 0
        #     index = indexes[0]
        #     while index.parent().isValid():
        #         index = index.parent()
        #         level += 1

        right_click_menu = QMenu()
        delAction = right_click_menu.addAction(self.tr("Delete"))
        delAction.triggered.connect(partial(self.item_delete, item))
        allAction = right_click_menu.addAction(self.tr("Select all"))
        allAction.triggered.connect(partial(self.selectAll))

        viewport = self.sender().viewport().mapToGlobal(position)
        right_click_menu.exec(viewport)
    
    def print_item(self, item: QStandardItem):
        items = self.get_items_values(item)
        if items:
            for n, i in enumerate(items):
                print(n, i)
                if len(i) == 1:
                    self.print_item(i)
        
    def get_items_values(self, item: QStandardItem) -> List[List[str]]:
        items: List[List[str]] = []
        while item.rowCount():
            row = item.takeRow(0)
            if row:
                items.append([i.text() for i in row if i])
        return items
    
    def get_items(self, item: QStandardItem) -> List[List[QStandardItem]]:
        items: List[List[QStandardItem]] = []
        while item.rowCount():
            row = item.takeRow(0)
            if row:
                items.append([i for i in row if i])
        return items
    
    def read_items(self, item: QStandardItem) -> List[List[QStandardItem]]:
        items: List[List[QStandardItem]] = []
        for row in range(item.rowCount()):
            itemRow: List[QStandardItem] = []
            for col in range(item.columnCount()):
                child = item.child(row, col)
                if child:
                    itemRow.append(child)
            items.append(itemRow)
        return items
    
    def read_item_rows(self, item: QStandardItem) -> List[List[QStandardItem]]:
        items: List[List[QStandardItem]] = []
        for row in range(item.rowCount()):
            itemRow: List[QStandardItem] = []
            for col in range(item.columnCount()):
                child = item.child(row, col)
                if child:
                    itemRow.append(child)
            items.append(itemRow)
        return items
    
    def _delete_recursive(self, item: QStandardItem) -> None:
        childs = self.get_items(item)
        if childs:
            for child in childs:
                if len(child) != 1 and child[-1].text():
                    # print([i.text() for i in child])
                    afileId = int(child[-1].text())
                    del self.afiles[afileId]
                else:
                    if child[0] is not None:
                        self._delete_recursive(child[0])
            
            self._delete_recursive(item)
        else:
            p = item.parent()
            if not p:
                p = self.rootParent
            
            row = p.takeRow(item.row())
            if len(row) > 1 and row[-1].text():
                afileId = int(row[-1].text())
                del self.afiles[afileId]

    def item_delete(self, item: QStandardItem) -> None:
        indexes = self.selectedIndexes()
        for n, idx in enumerate(indexes):
            if idx.data():
                self._delete_recursive(self.modelRow.itemFromIndex(idx))
        
        if item.parent():
            item.parent().removeRow(item.row())
        else:
            self.rootParent.removeRow(item.row())
