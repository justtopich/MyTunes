from typing import Callable, Tuple

from PyQt6.QtCore import QThread


class QThreadTarget(QThread):
    def __init__(self, target: Callable, args: Tuple[any, ...] = tuple()):
        super().__init__()
        self.target = target
        self.args = args
    
    def run(self):
        if self.target:
            self.target(*self.args)
