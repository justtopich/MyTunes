import glob
import os
import traceback
from functools import partial
from typing import Dict, List, Tuple, Set

from PyQt6.QtCore import QItemSelectionModel, Qt, QPoint, QItemSelection, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QDropEvent, QDragMoveEvent, QDragEnterEvent, QColor
from PyQt6.QtWidgets import QTreeView, QMenu, QAbstractItemView

from config import log, KNOWN_FORMAT
from service.tagEditor import TagEditor, AudioFile, TAGS, Tag
from .popup import ErrorBox
from .tagsLayout import TagsLayout
from myTunes.service.afileState import AfileState, Acover
from myTunes.service.util import get_afile_img, ImageInfo


COLUMNS_HIDE = ('Comment', 'Lyrics', 'isrc', 'afileId')
COLUMNS_EXT = ('Codec', 'Bitrate kbp/s', 'Samplerate kHz/s', 'Cover', 'afileId')
COLUMNS = ('Filename',) + tuple(i.title for i in TAGS) + COLUMNS_EXT


class TreeView(QTreeView):
    """
     Attributes:
         parent: root QStandardItem for files
         afiles: links to afile
         afileTree: afile metadata in treeview
    """

    def __init__(self, afileState: AfileState):
        super().__init__()
        self.tagsLayout: TagsLayout = None
        self.modelRow = QStandardItemModel()
        self.setModel(self.modelRow)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.modelRow.setHorizontalHeaderLabels(COLUMNS)
        self.header().setDefaultSectionSize(80)
        self.setColumnWidth(0, 300)
        self.setAlternatingRowColors(True)

        for i in range(1, 4): self.setColumnWidth(i, 150)
        for i in range(5, 11): self.setColumnWidth(i, 40)

        self.headerTag: Dict[int, Tag] = {}
        self._set_tag_index()
        for i in COLUMNS_HIDE: self.hideColumn(COLUMNS.index(i))
        self.afileIdHeaderIdx = self.header().model().columnCount() - 1
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

        self.rootParent = self.modelRow.invisibleRootItem()
        self.afileState = afileState
        self.tagEditor = TagEditor()
        self.selectedRows: List[Tuple[QStandardItem, ...]] = []


    def _set_tag_index(self):
        for n, col in enumerate(COLUMNS):
            for tag in TAGS:
                if tag.title == col or tag.name == col:
                    tag.index = n
                    self.headerTag[n] = tag
                    break

    def _get_selected_rows(self) -> List[Tuple[QStandardItem, ...]]:
        """
        Get rows by selected items. Mark all items in GUI as selected.

        Returns: List with rows as tuple[item, ...]. Rows length is fixed = model.headers.columnCount

        """
        model: QItemSelectionModel = self.selectionModel()
        rows: List[Tuple[QStandardItem, ...]] = []
        values: List[QStandardItem] = []
        rowIdx = -1
        rowHeads: Set[QModelIndex] = set()

        for index in model.selectedIndexes():
            item = self.modelRow.itemFromIndex(index)

            if item.row() != rowIdx:
                subRows = self.get_rows(item)
                if subRows:
                    for subRow in subRows:
                        rowIndex = self.modelRow.indexFromItem(subRow[0])
                        if rowIndex not in rowHeads:
                            rows.append(subRow)
                            rowHeads.add(rowIdx)

                if values and self.modelRow.indexFromItem(values[0]) not in rowHeads:
                    rows.append(tuple(values))
                    rowHeads.add(self.modelRow.indexFromItem(values[0]))
                rowIdx = item.row()
                values.clear()

        if values and self.modelRow.indexFromItem(values[0]) not in rowHeads:
            values.extend((None for _ in range(self.modelRow.columnCount() - len(values))))

            rows.append(tuple(values))
            rowHeads.add(self.modelRow.indexFromItem(values[0]))

        return rows

    def _set_rows_color(self, rows: List[Tuple[QStandardItem, ...]], color: QColor = None) -> None:
        for row in rows:
            for item in row:
                if item:
                    if color:
                        item.setBackground(color)
                    else:
                        item.setData(None, Qt.ItemDataRole.BackgroundRole)

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        if not hasattr(self, 'afileState') or not selected.indexes():
            return

        self.afileState.selectedAfilesId.clear()
        afileIdColumn = self.modelRow.columnCount() - 1
        self._set_rows_color(self.selectedRows)
        rows = self._get_selected_rows()
        self.selectedRows = rows

        if not rows:
            if self.tagsLayout is not None:
                self.tagsLayout.update_state()
            return

        self._set_rows_color(rows, QColor("lightblue"))

        afiles: List[AudioFile] = []
        selectedAfilesId: List[int] = []
        for row in rows:
            log.debug("select %s " % row[0].text())

            # root item always have max columns
            if len(row) > 1 and row[afileIdColumn] and row[afileIdColumn].text():
                aFileId = row[afileIdColumn].text()
                if int(aFileId) in self.afileState.afiles:
                    aFileId = int(aFileId)
                    afiles.append(self.afileState.afiles[aFileId])
                    selectedAfilesId.append(aFileId)

        self.afileState.selectedAfilesId = selectedAfilesId
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

    def _get_img_type(self, afile: AudioFile) -> str:
        imgType = '-'

        try:
            img = get_afile_img(afile)
        except Exception as e:
            log.error('load cover: %s' % e)
        else:
            if img:
                try:
                    imgType = ImageInfo(img).format
                except Exception as e:
                    log.error('image info: %s' % e)
                    imgType = '?'

        return imgType

    def _make_row(self, file: str) -> List[QStandardItem]:
        row: List[QStandardItem] = [QStandardItem(os.path.basename(file))]

        try:
            metadata: AudioFile = self.tagEditor.load_file(file)
        except Exception as e:
            print(traceback.format_exc())
            msg = f'load file tags: {file}: {e}'
            log.error(msg)
            raise Exception(msg)

        for n in range(1, self.header().model().columnCount() - len(COLUMNS_EXT)):
            tag: Tag = self.headerTag.get(n)

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

        # tech info
        codec = ''
        try:
            codec = metadata['#codec'].first
        except:
            pass

        if not codec:
            try:
                codec = metadata.mfile.mime[0]
            except:
                log.error("unknown codec: %s" % file)
        row.append(QStandardItem(codec))

        value = ''
        try:
            value = str(int(metadata['#bitrate'].first / 1000))
        except:
            pass

        if not value:
            try:
                size = os.path.getsize(file)
                length = metadata.mfile.info.length
                value = str(int((size*8/length)/1000))
            except:
                log.error("can't read tech info bitrate from %s" % file)

        row.append(QStandardItem(value))

        value = ''
        try:
            value = str(round(metadata.mfile.info.sample_rate/1000, 2))
        except Exception as e:
            log.error("can't read tech info samplerate from %s: %s" % (file, e))
        finally:
            row.append(QStandardItem(value))

        imgType = self._get_img_type(metadata)
        row.append(QStandardItem(imgType))

        afileId = max(self.afileState.afiles.keys()) + 1
        row.append(QStandardItem(str(afileId)))

        metadata.qTreeViewRow = row
        self.afileState.afiles[afileId] = metadata
        self.afileState.acovers[afileId] = Acover()

        return row

    def pass_file(self, uFile: str) -> bool:
        ext = uFile[uFile.rfind('.') + 1:].lower()
        return ext in KNOWN_FORMAT

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Adds rows to treeView.
        All rows adds to the self.rootParent. Each folder is a new parent.
        Parent columns count = nested columns. If not nested - self count
        Columns count can see by self.header().model().columnCount()

        Args:
            event: drop event

        Returns: None
        """

        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

            parents: Dict[str, QStandardItem] = {}
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    uFile = url.toLocalFile()
                    parent = self.rootParent

                    if os.path.isfile(uFile):
                        if self.pass_file(uFile):
                            log.debug(f'add root file {uFile}')
                            try:
                                parent.appendRow(self._make_row(uFile))
                            except Exception as e:
                                ErrorBox('Import error',str(e)).exec()
                    else:
                        log.debug(f'add root path {uFile}')
                        parent.appendRow((
                            QStandardItem(os.path.basename(uFile))
                        ))
                        parents[uFile] = parent.child(parent.rowCount() - 1)

                        for uFile in glob.iglob(f'{glob.escape(url.toLocalFile())}/**/*', recursive=True):
                            uFile = uFile.replace('\\', '/', -1)

                            if os.path.isfile(uFile):
                                if not self.pass_file(uFile):
                                    continue

                                log.debug(f'add file {uFile}')
                                try:
                                    parents[os.path.dirname(uFile)].appendRow(self._make_row(uFile))
                                except Exception as e:
                                    ErrorBox('Import error',str(e)).exec()
                            else:
                                newParent = QStandardItem(os.path.basename(uFile))
                                parents[os.path.dirname(uFile)].appendRow(newParent)
                                parents[uFile] = newParent
                                log.debug(f'add path {newParent.text()}')

                for i in parents.values():
                    self.setExpanded(i.index(), True)
            else:
                event.ignore()

    def open_menu(self, position: QPoint) -> None:
        # indexes = self.sender().selectedIndexes()
        itemIdx = self.indexAt(position)

        if not itemIdx.isValid():
            return

        item = self.modelRow.itemFromIndex(itemIdx)
        # if len(indexes) > 0:
        #     level = 0
        #     index = indexes[0]
        #     while index.parent().isValid():
        #         index = index.parent()
        #         level += 1

        right_click_menu = QMenu()
        delAction = right_click_menu.addAction(self.tr("Delete"))
        delAction.triggered.connect(partial(self.item_delete, item, itemIdx))
        allAction = right_click_menu.addAction(self.tr("Select all"))
        allAction.triggered.connect(partial(self.selectAll))

        viewport = self.sender().viewport().mapToGlobal(position)
        right_click_menu.exec(viewport)

    def item_delete(self, item: QStandardItem, itemIdx: QModelIndex) -> None:
        # selected = self.selectionModel().selectedRows()
        #
        # rows: List[tuple[QStandardItem, ...]] = []
        # for select in selected:
        #     rows.extend(self.get_rows(self.modelRow.itemFromIndex(select)))

        self.clearSelection()
        rows = self.get_rows(item)

        # delete from nested rows firstly
        for n, row in enumerate(rows[::-1]):
            rowIdx: QModelIndex = self.modelRow.indexFromItem(row[0])
            parent: QModelIndex = rowIdx.parent()
            log.debug('remove %s' % row[0].text())

            if row[self.afileIdHeaderIdx] and row[self.afileIdHeaderIdx].text():
                afileId = int(row[self.afileIdHeaderIdx].text())
                del self.afileState.afiles[afileId]
                del self.afileState.acovers[afileId]

            self.modelRow.removeRow(rowIdx.row(), parent)

        self.selectedRows.clear()
        self.clearSelection()
        self.tagsLayout.update_state()

    def get_rows(self, item: QStandardItem, maxLevel=300, onlyChilds=False, _level=0) -> list[tuple[QStandardItem, ...]]:
        """
        get rows from item

        Args:
            item: start from
            onlyChilds: if True will return only childs rows else first row will ve current item.row
            maxLevel: max level for recursion to get childs

        Returns: List with rows as tuple[item, ...]. Rows length is fixed = model.headers.columnCount

        """
        items: list[tuple[QStandardItem | None, ...], ...]
        parent = item.parent() or self.rootParent
        model = self.model()

        if onlyChilds:
            items = []
        else:
            items = [tuple([parent.child(item.row(), col) for col in range(model.columnCount())])]

        if _level < maxLevel:
            itemsRow: List[QStandardItem, ...] = []

            for row in range(item.rowCount()):
                for col in range(item.columnCount()):
                    if not item.child(row, col):
                        itemsRow.append(None)
                        continue

                    if col == 0 and item.child(row, col).hasChildren():
                        items.extend(
                            self.get_rows(
                                item=item.child(row, col),
                                maxLevel=maxLevel,
                                _level=_level+1)
                        )
                    else:
                        itemsRow.append(item.child(row, col))

                if itemsRow:
                    if itemsRow[0] and itemsRow[0].text():
                        if len(itemsRow) < self.modelRow.columnCount():
                            itemsRow.extend((None for _ in range(self.modelRow.columnCount() - len(itemsRow))))

                        items.append(tuple(itemsRow))
                    itemsRow.clear()
        return items
