from typing import Callable, Tuple

from PyQt6.QtCore import QThread

"""
Qt widgets are not thread safe. But QThread not work correctly in pyinstaller.
look https://groups.google.com/g/python_inside_maya/c/D78HV6jDdwk?pli=1

When you have multiple long-running tasks within your application,
with each calling QApplication.processEvents() to keep things ticking,
your application's behavior can be unpredictable.
"""


class QThreadTarget(QThread):
    def __init__(self, target: Callable, args: Tuple[any, ...] = tuple()):
        super().__init__()
        self.target = target
        self.args = args
    
    def run(self):
        if self.target:
            self.target(*self.args)
