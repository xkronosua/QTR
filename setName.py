# _*_ coding: utf-8 _*_
from ui.Ui_setName import Ui_Dialog
from PyQt4 import QtGui
import os
import scipy as sp

class NameDialog(QtGui.QDialog):
	name = ''
	def __init__(self, parent=None, name=''):
		super(NameDialog, self).__init__(parent)
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		self.name = name
		self.ui.name.setText(name)
		self.ui.Ok.clicked.connect(self.okClicked)

	def okClicked(self):
		self.name = self.ui.name.text()
		self.close()
