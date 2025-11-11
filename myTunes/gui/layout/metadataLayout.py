import os.path
import re
import shutil
from typing import List, Dict, Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QStandardItem
from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QDialogButtonBox, QWidget, QCheckBox, \
    QLineEdit, QFileDialog
from music_tag import AudioFile

from config import cfg, log
from service.tagEditor import TAGS
from service.converterTask import ConverterTask
from gui.layout.treeView import TreeView
from gui.layout.iconButton import IconButton
from gui.layout.processWindow import ProcessWindow
from gui.layout.saveWindow import SaveWindow
from myTunes.service.converter import Converter, Encoder
from myTunes.gui.layout.popup import ErrorBox
from .coverLayout import CoverLayout
from myTunes.model.settings import CoverSettings
from myTunes.service.afileState import AfileState

__all__ = ('MetadataLayout',)


class MetadataLayout(QVBoxLayout):
    def __init__(self, converter: Converter, coverLayout: CoverLayout, afileState: AfileState):
        super(MetadataLayout, self).__init__()
        self._converter = converter
        self._parameterLayout: List[QHBoxLayout] = []
        self._parameters: List[QWidget] = []
        self._activeEncoder: Encoder = None
        self._treeView: TreeView = None
        self._coverLayout = coverLayout
        self._afileState = afileState

        self._coverLayout.buttonSave.clicked.connect(self.save_afile_cover)

        self.processWindow = ProcessWindow(converter)
        self.saveWindow = SaveWindow(self._afileState)

        group = QHBoxLayout()
        
        self.buttonRename = QDialogButtonBox()
        self.buttonRename.addButton('Rename', QDialogButtonBox.ButtonRole.ApplyRole)
        self.buttonRename.clicked.connect(self.rename_files)
        group.addWidget(self.buttonRename)
        
        self.buttonSave = QDialogButtonBox(QDialogButtonBox.StandardButton.Save)
        self.buttonSave.accepted.connect(self.save_afile_meta)
        group.addWidget(self.buttonSave)

        self.buttonStart = QDialogButtonBox()
        self.buttonStart.addButton('Start', QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttonStart.accepted.connect(self.start)
        group.addWidget(self.buttonStart)
        self.addLayout(group)
        
        self.outputFolder = QLineEdit("")
        self.outputFolder.setMinimumWidth(200)
        group = QHBoxLayout()
        group.addWidget(QLabel('Ouput folder:'), Qt.AlignmentFlag.AlignRight)
        group.addWidget(self.outputFolder)
        self.buttonOuput = IconButton()
        self.buttonOuput.clicked.connect(self.set_output_folder)
        with open('resource/folder.png', mode='rb') as f:
            icon = QPixmap()
            icon.loadFromData(f.read())
            icon = icon.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.buttonOuput.setPixmap(icon)
            self.buttonOuput.setMaximumWidth(30)
            group.addWidget(self.buttonOuput)
        self.addLayout(group)

        self.renameFilesMask = QComboBox()
        self.renameFilesMask.setEditable(True)
        self.renameFilesMask.setMinimumWidth(200)
        self.renameFilesMask.addItems((
            '<Artist> - <Title>',
            '<#>. <Artist> - <Title>',
            '<#>. <Title>',
            '<#>. <Title> (<Artist>)',
            '<Artist> - <Album> - <#> - <Title>',
        ))
        group = QHBoxLayout()
        group.addWidget(QLabel('Rename files mask:'), Qt.AlignmentFlag.AlignRight)
        group.addWidget(self.renameFilesMask)
        self.addLayout(group)

        encoderLayout = QHBoxLayout()
        self.encoder = QComboBox()
        self.encoder.addItems(converter.encoderName.keys())
        self.encoder.activated[int].connect(self.update_encoder)
        encoderLayout.addWidget(QLabel(f'Encoder:'), Qt.AlignmentFlag.AlignLeft)
        encoderLayout.addWidget(self.encoder, Qt.AlignmentFlag.AlignLeft)

        self.addLayout(encoderLayout)
        self.update_encoder(0)

    def set_treeView(self, treeView: TreeView) -> None:
        self._treeView = treeView

    def _save_afile(self, coverMode: bool) -> None:
        afileId = self._treeView.tagsLayout.tags['afileId'].text()
        if not afileId:
            return

        afiles = [self._afileState.afiles[i] for i in self._afileState.selectedAfilesId]

        self.enable_controls(False)
        self.saveWindow.create_window()
        self.saveWindow.process(afiles=afiles, treeView=self._treeView, coverMode=coverMode)
        self._coverLayout.jpegNext.setEnabled(False)
        self.enable_controls(True)

    def save_afile_meta(self) -> None:
        self._save_afile(False)

    def save_afile_cover(self) -> None:
        self._save_afile(True)

    def _check_rename_mask(self, mask: str) -> List[str]:
        tags = [f'<{i.title.lower()}>' for i in TAGS]
        match = re.findall(r'<[^<>]+>', mask)
        for i in match:
            assert i.lower() in tags, f'Unknown tag {i}'
        return match

    def rename_files(self) -> None:
        mask = self.renameFilesMask.currentText()
        if mask:
            try:
                match = self._check_rename_mask(mask)
            except AssertionError as e:
                ErrorBox(
                    'Rename error',
                    'not valid mask',
                    str(e)
                ).exec()
            else:
                row = -1
                for i in self._treeView.selectedIndexes():
                    if i.row() != row:
                        self._rename_files(self._treeView.modelRow.itemFromIndex(i), match)
                        row = i.row()
    
    def _rename_files(self, item: QStandardItem, match: Iterable[str]) -> None:
        rows = self._treeView.selectedRows
        if not rows: return

        for row in rows:
            if row[self._treeView.afileIdHeaderIdx] is None:
                continue

            afileId = int(row[self._treeView.afileIdHeaderIdx].text())
            afile = self._afileState.afiles[afileId]

            fileName = self.renameFilesMask.currentText().lower()
            for tag in TAGS:
                for i in match:
                    i = i.lower()
                    if f'<{tag.title.lower()}>' == i:
                        val = afile[tag.name].first
                        if val is None:
                            val = ''
                        fileName = fileName.replace(i, str(val), -1)

            fileName = f'{fileName}{afile.filename[afile.filename.rfind("."):]}'
            fileName = f'{os.path.dirname(afile.filename)}/{fileName}'

            try:
                shutil.move(afile.filename, fileName)
            except Exception as e:
                log.error('rename file %s: %s' % (os.path.basename(afile.filename), e))
            else:
                log.info('rename file %s -> %s' % (os.path.basename(afile.filename), os.path.basename(fileName)))
                metadata: AudioFile = self._treeView.tagEditor.load_file(fileName)
                metadata.qTreeViewRow = afile.qTreeViewRow
                self._afileState.afiles[afileId] = metadata
                row[0].setText(os.path.basename(fileName))

    def _take_tasks_recursive(self, item: QStandardItem, tasks: List[ConverterTask], path:str='') -> List[ConverterTask]:
        model = self._treeView.model()

        if item == self._treeView.rootParent:
            rows = []
            for row in range(model.rowCount()):
                rows.append(tuple(item.child(row, col) for col in range(model.columnCount())))
        else:
            rows = self._treeView.get_rows(item, maxLevel=1, onlyChilds=True)

        for row in rows:
            if row[0].hasChildren():
                self._take_tasks_recursive(row[0], tasks, f'{path}/{row[0].text()}')
                continue
            elif row[model.columnCount() - 1] is not None:
                afileId = int(row[-1].text())
                ext = self._activeEncoder.settings.format
                tasks.append(ConverterTask(
                    afile=self._afileState.afiles[afileId],
                    qTreePath=path,
                    ext=ext
                ))
        return tasks

    def set_output_folder(self) -> None:
        dir = QFileDialog.getExistingDirectory()
        if dir:
            self.outputFolder.setText(dir)

    def start(self) -> None:
        paramMap = self._activeEncoder.settings.guiSettings
        settings: Dict[str, any] = {}
        # coverSettings = CoverSettings(
        #     jpegNext=self._coverLayout.jpegNext.isChecked(),
        #     quality=int(self._coverLayout.quality.currentText())
        # )

        # update exe settings
        self._converter.ffmpeg.exe = cfg.ffmpeg
        self._converter.qaac.exe = cfg.qaac
        # self._converter.coverSettings = coverSettings

        for param in self._parameters:
            if isinstance(param, QCheckBox):
                value = bool(param.isChecked())
            else:
                value = param.currentText()

            name = param.objectName()
            # print(name, value)

            attr = paramMap[name]['attr']
            attrVal = self._activeEncoder.settings.__getattribute__(attr)
            if isinstance(attrVal, int):
                value = int(value)
            elif isinstance(attrVal, float):
                value = int(value)

            settings[attr] = value

        try:
            self._activeEncoder.load_settings(settings)
        except Exception as e:
            ErrorBox(
                'Encoder error',
                'not valid parameters',
                str(e)
            ).exec()
        else:
            self.enable_controls(False)
            print('encoder setting updated')
            tasks = self._take_tasks_recursive(self._treeView.rootParent, [])
            self.enable_controls(False)
            self.processWindow.create_window()
            self.processWindow.process(tasks, self.outputFolder.text())
            self.enable_controls(True)

    def enable_controls(self, on:bool):
        self.buttonStart.setEnabled(on)
        self.buttonSave.setEnabled(on)
        self.buttonRename.setEnabled(on)
        self.processWindow.buttonClose.setEnabled(on)
        self.processWindow.buttonStop.setEnabled(on is False)
        
    def clear_layout(self, layout: QHBoxLayout) -> None:
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def update_encoder(self, index:int) -> None:
        encoder = self._converter.encoderName[self.encoder.itemText(index)]
        print('set encoder', encoder.name)

        if encoder.name == 'QAAC':
            self._activeEncoder = self._converter.qaac
        else:
            self._activeEncoder = self._converter.ffmpeg
        
        self._converter.encoder = self._activeEncoder

        for lo in self._parameterLayout:
            self.clear_layout(lo)

        self._parameterLayout.clear()
        self._parameters.clear()

        for k in encoder.settings.guiSettings.keys():
            v = encoder.settings.guiSettings[k]['value']
            print(k, v)

            if isinstance(v, bool):
                param = QCheckBox()
                param.setChecked(v)
            else:
                param = QComboBox()
                param.addItems(v)
                # param.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
                param.setMinimumSize(len(max(v, key=len))*12, 20)

            param.setObjectName(k)
            # param.setMinimumSize(QSize(60, 10))
            # param.activated[int].connect(self.update_main)

            group = QHBoxLayout()
            group.addWidget(QLabel(f'{k}:'), Qt.AlignmentFlag.AlignRight)
            group.addWidget(param)
            
            self.addLayout(group)
            self._parameterLayout.append(group)
            self._parameters.append(param)
