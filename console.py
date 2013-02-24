# _*_ coding: utf-8 _*_
from ui.Ui_console import Ui_Dialog
from PyQt4 import QtGui
#import os
#import scipy as sp

class scriptDialog(QtGui.QDialog):
	
	def __init__(self, parent=None, name=''):
		super(scriptDialog, self).__init__(parent)
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		self.ui.Close.clicked.connect(self.close)
		self.ui.Exec.clicked.connect(self.Exec)
		
	def Exec(self):
		code = self.ui.editor.toPlainText()
		string_func = \
"""def func(self=self):
	get_data = self.parent().getData
	update_data = self.parent().updateData
	import scipy as sp
	______________________________________
"""
		if code:
			txt = '\n'+'\t'
			for i in code.split('\n'):
				txt += i + "\n" + '\t' 
		
			string_func += txt
			print(string_func)
			exec(string_func)
			f = locals()["func"]
			f()
			print(string_func)
			#self.close()
			
