from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QCheckBox, QComboBox, QVBoxLayout, QWidget, QDialogButtonBox

from .imageLabel import ImageLabel
from myTunes.service.afileState import AfileState
from config import log


class CoverLayout(QWidget):
    def __init__(self, afileState: AfileState):
        super(CoverLayout, self).__init__()

        self.afileState = afileState
        self.adjustSize()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.quality = QComboBox()
        self.jpegNext = QCheckBox()
        self.jpegNext.setDisabled(True)
        self.jpegNext.setChecked(True)

        self.jpegNext.toggled.connect(self.on_click_jpegNext)
        self.quality.currentTextChanged.connect(self.on_change_quality)

        self.cover = ImageLabel(afileState, self.jpegNext, self.quality)
        layout.addWidget(self.cover, Qt.AlignmentFlag.AlignLeft)

        group = QHBoxLayout()
        self.buttonSave = QDialogButtonBox(QDialogButtonBox.StandardButton.Save)
        group.addWidget(self.buttonSave, Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(group)

        group = QHBoxLayout()
        group.addWidget(self.jpegNext)
        group.addWidget(QLabel('Progressive JPEG'), Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(group)

        group = QHBoxLayout()
        group.setSpacing(5)
        group.setContentsMargins(0, 0, 0, 0)
        label = QLabel('Quality:')

        self.quality.setMaximumSize(60, 40)
        self.quality.addItems(('15','30','45','60','75','95', '100'))
        self.quality.setCurrentText('100')

        group.addWidget(label)
        group.addWidget(self.quality)
        group.addStretch()
        layout.addLayout(group)
        layout.addStretch()

        screenSize = QGuiApplication.primaryScreen().geometry()
        height = screenSize.height()
        width = screenSize.width()
        self.setMaximumSize(int(height/5), int(width/5))

    def on_click_jpegNext(self, checked:bool):
        self._log_state()

        for i in self.afileState.selectedAfilesId:
            self.afileState.acovers[i].jpegNext = checked

    def _log_state(self):
        log.debug('%s JPEG (Progressive=%s, quality=%s) for afiles %s' %
            ('check' if self.jpegNext.checkState() else 'unchecked',
                self.jpegNext.checkState(),
                self.quality.currentText(),
                self.afileState.selectedAfilesId
            )
        )
        self.buttonSave.setEnabled(not self.cover.isDefault)

    def on_change_quality(self, text):
        self._log_state()

        for i in self.afileState.selectedAfilesId:
            self.afileState.acovers[i].quality = int(text)

        self.jpegNext.setEnabled(text != '100')

    def show_state(self, s):
        print(s == Qt.CheckState.Checked.value)
        print(s)
