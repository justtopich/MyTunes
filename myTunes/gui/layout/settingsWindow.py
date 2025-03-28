import os.path

from PIL.ImageQt import QPixmap
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDialogButtonBox, QLineEdit, QLabel, QFileDialog, \
    QComboBox

from gui.layout.iconButton import IconButton
from config import cfg


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Settings')
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)

        self.ffmpegFolder = QLineEdit(cfg.ffmpeg)
        self.ffmpegFolder.setMinimumWidth(300)
        group = QHBoxLayout()
        group.addWidget(QLabel('ffmpeg:'), Qt.AlignmentFlag.AlignRight)
        group.addWidget(self.ffmpegFolder)
        self.buttonOuput = IconButton()
        self.buttonOuput.clicked.connect(self.set_ffmpeg)
        with open('resource/folder.png', mode='rb') as f:
            icon = QPixmap()
            icon.loadFromData(f.read())
            icon = icon.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.buttonOuput.setPixmap(icon)
            self.buttonOuput.setMaximumWidth(30)
            group.addWidget(self.buttonOuput)
        layout.addLayout(group)

        self.qaacFolder = QLineEdit(cfg.qaac)
        self.qaacFolder.setMinimumWidth(300)
        group = QHBoxLayout()
        group.addWidget(QLabel('QAAC:'), Qt.AlignmentFlag.AlignRight)
        group.addWidget(self.qaacFolder)
        self.buttonOuput = IconButton()
        self.buttonOuput.clicked.connect(self.set_qaac)
        with open('resource/folder.png', mode='rb') as f:
            icon = QPixmap()
            icon.loadFromData(f.read())
            icon = icon.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.buttonOuput.setPixmap(icon)
            self.buttonOuput.setMaximumWidth(30)
            group.addWidget(self.buttonOuput)
        layout.addLayout(group)

        group = QHBoxLayout()
        self.cpuThreads = QComboBox()
        self.cpuThreads.addItems(str(i) for i in range(1,os.cpu_count() + 1))
        self.cpuThreads.setCurrentText(str(cfg.threads))
        group.addWidget(QLabel('CPU Threads: '), Qt.AlignmentFlag.AlignRight)
        group.addWidget(self.cpuThreads)
        layout.addLayout(group)

        group = QHBoxLayout()
        group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.buttonClose = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.buttonClose.clicked.connect(self.close)
        group.addWidget(self.buttonClose)

        self.buttonSave = QDialogButtonBox(QDialogButtonBox.StandardButton.Save)
        self.buttonSave.clicked.connect(self.save)
        group.addWidget(self.buttonSave)

        layout.addLayout(group)

    def set_ffmpeg(self, tri) -> None:
        file: tuple[QUrl, str] = QFileDialog.getOpenFileUrl()
        if file:
            self.ffmpegFolder.setText(file[0].toLocalFile())

    def set_qaac(self, tri) -> None:
        file: tuple[QUrl, str] = QFileDialog.getOpenFileUrl()
        if file:
            self.qaacFolder.setText(file[0].toLocalFile())

    def save(self):
        cfg.qaac = self.qaacFolder.text()
        cfg.ffmpeg = self.ffmpegFolder.text()
        cfg.threads = int(self.cpuThreads.currentText())
        cfg.save()
        self.close()