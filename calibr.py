# _*_ coding: utf-8 _*_

from ui.calibrDialog import Ui_Dialog
from PyQt4 import QtGui#, QtCore, uic
from glue_designer import DesignerMainWindow
import scipy as sp
import os

class CalibrDialog(QtGui.QDialog):
	K = 0.
	Root = "./"
	fileList = []
	data = []
	activeIndex = 0
	def __init__(self, Root = "./"):
		super(CalibrDialog, self).__init__()
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		self.Root = Root
		
		self.qcut = DesignerMainWindow()
		self.fileDialog = QtGui.QFileDialog(self)
		self.ui.calc.setEnabled(False)
		#self.ui.res.setEnabled(False)
		self.ui.file.clicked.connect(self.getFile)
		self.qcut.dataChanged.connect(self.getBackFromQcut)
		self.ui.calc.clicked.connect(self.recalcRes)
		self.ui.namesList.currentRowChanged[int].connect(self.plotCurrent)

	def getBackFromQcut(self):
		data= self.qcut.getData()
		self.data[self.activeIndex][0] = data
	def plotCurrent(self, index):
		self.activeIndex = index
		self.qcut.show()
		self.qcut.Plot(self.data[index][0])
		
	def recalcRes(self):
		
		if len(self.data)>=1:
			X, Y = [], []
			for data in self.data:
				X.append(data[0][:,1].mean())
				Y.append(data[1])
			k = sp.polyfit(X, Y, 1)[0]
			if k:
				self.K = k
				self.ui.res.setText(str(k))
		#except: print('Error')

	def getFile(self):
		Path = self.fileDialog.getOpenFileNames(self,'Open File', self.Root)
		self.ui.namesList.clear()
		if len(Path)>=1:
			data = []
			for i in Path:
				name = os.path.basename(i).split('.')[0]
				self.ui.namesList.addItem(name)
				tmp = sp.loadtxt(i)
				if name == "Null":
					name = '0000'
				try:	
					power = float(name)/100.
					data.append([tmp, power])
				except: pass
			if len(data)>=1:
				self.data = data
				self.ui.calc.setEnabled(True)
				
			'''
			print(path,sp.loadtxt(path))
			try:
				data = sp.loadtxt(path)
			except:
				print('Error')
			if not data is None:
				self.data = data
				self.ui.calc.setEnabled(True)
				self.qcut.show()
				self.qcut.Plot(data)
			'''
