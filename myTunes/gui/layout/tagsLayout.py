from typing import Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QLineEdit, QGridLayout

from gui.layout.popup import ErrorBox
from myTunes.service.tagEditor import AudioFile, TAGS, Tag
from myTunes.config import log
from .coverLayout import CoverLayout
from myTunes.service.util import get_afile_img


class TagsLayout(QGridLayout):
    def __init__(self, treeView: 'TreeView', coverLayout: CoverLayout):
        super(TagsLayout, self).__init__()
        self._treeView = treeView
        self.tags: Dict[str, QLineEdit] = {}
        self.coverLayout = coverLayout
        colMax = 3 * 2 - 1

        row = 0
        col = 0
        for tag in TAGS:
            if col > colMax:
                row += 1
                col = 0

            self.tags[tag.name] = QLineEdit("")
            # print(f'{row}, {col}, {tag.name}')
            self.add_tag_line(row, col, tag)
            col += 2

        afileIdIdx = QLineEdit("")
        afileIdIdx.hide()
        self.addWidget(afileIdIdx, row, col + 1, )
        self.tags['afileId'] = afileIdIdx

    def add_tag_line(self, row: int, col: int, tag: Tag) -> None:
        self.addWidget(QLabel(f'{tag.title}:'), row, col, Qt.AlignmentFlag.AlignRight)
        # self.addWidget(getattr(self, name), index, 1+col)
        self.addWidget(self.tags[tag.name], row, col+1)

    def load_cover(self, afile: AudioFile, afileId: int) -> None:
        acover = self._treeView.afileState.acovers[afileId]

        if acover.path:
            with open(acover.path, 'rb') as f:
                cover = f.read()
        else:

            try:
                cover = get_afile_img(afile)
            except Exception as e:
                log.error(f'load cover from {afile.filename}: {e}')
                ErrorBox(f"Can't load cover", str(e)).exec()
                cover = self.coverLayout.cover.defaultImg

        try:
            self.coverLayout.cover.set_image(cover, afileId)
        except Exception as e:
            log.error('show cover: %s' % e)

    def update_state(self, afiles: List[AudioFile] = None, afilesId: List[int] = None) -> None:
        if not afiles:
            self.tags['afileId'].setText('')
            self.coverLayout.cover.set_image()
            for tag in TAGS:
                self.tags[tag.name].setText('')
            return
        elif len(afiles) > 1:
            self.lock_tags()
        else:
            self.unlock_tags()

        # using first track cover when select a folder

        afile = afiles[0]
        afileId = afilesId[0]
        self.tags['afileId'].setText(str(afileId))
        
        for tag in TAGS:
            val = afile[tag.name].first
            if val is None:
                self.tags[tag.name].setText('')
            else:
                self.tags[tag.name].setText(str(val))

        self.load_cover(afile, afileId)

    def lock_tags(self):
        for tag in TAGS:
            if not tag.multiTag:
                self.tags[tag.name].setEnabled(False)

    def unlock_tags(self):
        for tag in TAGS:
            self.tags[tag.name].setEnabled(True)
            