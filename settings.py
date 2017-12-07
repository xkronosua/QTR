# _*_ coding: utf-8 _*_
from ui.Ui_settings import Ui_Dialog
from PyQt4 import QtGui
import os
import configparser


class SettingsDialog(QtGui.QDialog):
    # config = dict(length=0, typeExp=0)
    config = configparser.ConfigParser()
    path = './configs.cfg'

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.uiConnect()

        # Sections
        self.config['main'] = {
            'length': 0,
            'typeExp': 0}

        if os.path.exists(self.path):
            self.config.read(self.path)
            for i in self.config['main']:
                getattr(self.ui, i).setCurrentIndex(
                    int(self.config['main'][i]))

        self.uiConfig()

    def Close(self):
        self.close()

    def Ok(self):
        for i in self.config['main']:
            self.config['main'][i] = str(getattr(self.ui, i).currentIndex())

        # ------------------------------------------------
        with open(self.path, 'w') as configfile:
            self.config.write(configfile)

        self.close()

        self.uiConfig()

    '''
    def getDelimiter(self):
        delimiters = {
            'space': ' ',
            'space space': '  ',
            'tab': '\t',
            ',': ',',
            '.': '.',
            ';': ';'
            }
        return delimiters[self.ui.delimiter.currentText()]
    '''

    def uiConfig(self):
        self.parent().intensDialog.typeExp(self.ui.typeexp.currentIndex())
        self.parent().setLength(self.ui.length.currentText())

    def uiConnect(self):
        self.ui.Close.clicked.connect(self.Close)
        self.ui.Ok.clicked.connect(self.Ok)
