import os.path
import re
import shutil
import time
from threading import Thread
from typing import List, Dict, Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QStandardItem
from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QDialogButtonBox, QWidget, QCheckBox, \
    QLineEdit, QFileDialog
from music_tag import AudioFile

from service.tagEditor import TAGS
from service.converterTask import ConverterTask
from service.qThreadTarget import QThreadTarget
from gui.layout.treeView import TreeView
from gui.layout.iconButton import IconButton
from gui.layout.processWindow import ProcessWindow
from myTunes.service.converter import Converter, Encoder
from myTunes.gui.layout.popup import ErrorBox

__all__ = ('SettingsLayout',)


class SettingsLayout(QVBoxLayout):
    def __init__(self, converter: Converter):
        super(SettingsLayout, self).__init__()
        self._converter = converter
        self._parameterLayout: List[QHBoxLayout] = []
        self._parameters: List[QWidget] = []
        self._activeEncoder: Encoder = None
        self._treeView: TreeView = None
        self.processWindow = ProcessWindow(converter)
        
        group = QHBoxLayout()
        
        self.buttonRename = QDialogButtonBox()
        self.buttonRename.addButton('Rename', QDialogButtonBox.ButtonRole.ApplyRole)
        self.buttonRename.clicked.connect(self.rename_files)
        group.addWidget(self.buttonRename)
        
        self.buttonSave = QDialogButtonBox(QDialogButtonBox.StandardButton.Save)
        self.buttonSave.accepted.connect(self.save_afile)
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

    def save_afile(self) -> None:
        afileId = self._treeView.tagsLayout.tags['afileId'].text()
        if afileId != '':
            afiles = [self._treeView.afiles[i] for i in self._treeView.selectedAfilesId]
            fewFiles = len(afiles) > 1
            
            for afile in afiles:
                for tag in TAGS:
                    if fewFiles and not tag.multiTag:
                        continue

                    val = self._treeView.tagsLayout.tags[tag.name].text()
                    if val == '':
                        if tag.name in afile:
                            del afile[tag.name]
                    else:
                        val = afile.get(tag.name).type(val)
                        afile[tag.name] = val
                    
                    afile.qTreeViewRow[tag.index].setText(str(val))
                
                if not self._treeView.tagsLayout.cover.isDefault:
                    afile['artwork'] = self._treeView.tagsLayout.cover.img
                afile.save()

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
                for i in self._treeView.selectedIndexes():
                    self._rename_recursive(self._treeView.modelRow.itemFromIndex(i), match)
    
    def _rename_recursive(self, item: QStandardItem, match: Iterable[str]) -> None:
        childs = self._treeView.read_items(item)
        if childs:
            for child in childs:
                if len(child) != 1:
                    afileId = int(child[-1].text())
                else:
                    if child[0] is not None:
                        self._rename_recursive(child[0], match)
        else:
            p = item.parent()
            if not p: p = self._treeView.rootParent
            
            items = self._treeView.read_item_rows(p)
            row = items[item.row()]
            if row and row[-1] is not None:
                afileId = int(row[-1].text())
                afile = self._treeView.afiles[afileId]
                
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
                row[0].setText(fileName)
                fileName = f'{os.path.dirname(afile.filename)}/{fileName}'
                shutil.move(afile.filename, fileName)
                metadata: AudioFile = self._treeView.tagEditor.load_file(fileName)
                self._treeView.afiles[afileId] = metadata

    def _take_tasks_recursive(self, item: QStandardItem, tasks: List[ConverterTask], path:str='') -> List[ConverterTask]:
        childs = self._treeView.read_items(item)
        if childs:
            for child in childs:
                if len(child) != 1:
                    afileId = int(child[-1].text())
                    ext = self._activeEncoder.settings.format
                    
                    tasks.append(ConverterTask(
                        afile=self._treeView.afiles[afileId],
                        qTreePath=path,
                        ext=ext
                    ))
                else:
                    if child[0] is not None:
                        tasks = self._take_tasks_recursive(child[0], tasks, f'{path}/{child[0].text()}')
        return tasks

    def set_output_folder(self) -> None:
        dir = QFileDialog.getExistingDirectory()
        if dir:
            self.outputFolder.setText(dir)

    def start(self) -> None:
        paramMap = self._activeEncoder.settings.guiSettings
        settings: Dict[str, any] = {}

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
            self.processWindow.create_window()
            # QThreadTarget not work correctly in pyinstaller. look https://groups.google.com/g/python_inside_maya/c/D78HV6jDdwk?pli=1
            Thread(target=self.processWindow.process, args=(tasks, self.outputFolder.text(),)).start()
            Thread(target=self.wait_processing).start()

    def wait_processing(self):
        while not self.processWindow.allDone:
            time.sleep(.5)
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
