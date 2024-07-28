from PyQt6.QtWidgets import QMessageBox

__all__ = ('MessageBox', 'WarnBox', 'InfoBox', 'SubmitBox', 'ErrorBox')


class MessageBox(QMessageBox):
    def __init__(self, title: str, message: str, desc: str = None, details: str = None):
        super(MessageBox, self).__init__()
        self.setWindowTitle(title)
        self.setText(message)
        if desc: self.setInformativeText(desc)
        if details: self.setDetailedText(details)
        self.setStyleSheet("QDialogButtonBox {min-width: 200px; min-height: 50px; qproperty-centerButtons: true;}")


class WarnBox(MessageBox):
    def __init__(self, title: str, message: str, desc: str = None, details: str = None):
        super(WarnBox, self).__init__(title, message, desc, details)
        self.setIcon(QMessageBox.Icon.Warning)
        self.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)


class InfoBox(MessageBox):
    def __init__(self, title: str, message: str, desc: str = None, details: str = None):
        super(InfoBox, self).__init__(title, message, desc, details)
        self.setIcon(QMessageBox.Icon.Information)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        # self.buttonClicked.connect(msgbtn)


class ErrorBox(MessageBox):
    def __init__(self, title: str, message: str, desc: str = None, details: str = None):
        super(ErrorBox, self).__init__(title, message, desc, details)
        self.setIcon(QMessageBox.Icon.Critical)
        self.setStandardButtons(QMessageBox.StandardButton.Close)


class SubmitBox(MessageBox):
    def __init__(self, title: str, message: str, desc: str = None, details: str = None):
        super(SubmitBox, self).__init__(title, message, desc, details)
        self.setIcon(QMessageBox.Icon.Question)
