# _*_ coding: utf-8 _*_
from ui.Ui_intens import Ui_Dialog
from PyQt4 import QtGui#, QtCore
from math import pi, sqrt
from glue_designer import DesignerMainWindow
import scipy as sp
import os

class IntensDialog(QtGui.QDialog):
	Ai2 = 0.
	filters = 1.
	result = 0.
	outFilesNames = []
	# Змінні для калібровки
	K = 0.	# Коефіцієнт калібровки
	kPICODict = {b'1064':5.03*10**-3, b'532':0.002,b"633" : 0.003}
	Root = "./"
	calibrFilesList = []
	data = []
	activeIndex = 0
	
	def __init__(self, parent=None,  Root="./"):
		super(IntensDialog, self).__init__(parent)
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		self.ui.length.setValue(float(self.parent().LENGTH))
		
		self.Root = Root
		
		self.qcut = DesignerMainWindow()
		self.fileDialog = QtGui.QFileDialog(self)
		
		
		self.uiConnect()
		#self.ui.recalcAi2.setEnabled(False)
		#self.ui.Ai2.setEnabled(False)
		
	def applyForActiveData(self):
		xc = 0	#self.ui.xColumn.value()
		Name = self.ui.activeDataType.currentText()
		data = self.parent().getData(Name)
		if not data is None:
			data[:, xc] *= float(self.ui.result.text())
			self.parent().formatedUpdate(data, data.scale, data.Type, Name=data.Name)
		
	def applyFilt(self):
		'''Застосування фільтрів із бази'''
		#self.parent().filtersDict = self.parent().getFilters(length = self.parent().LENGTH)
		filtBaseNames = list(self.parent().filtersDict.keys())
		print(filtBaseNames)
		M = 1.
		active = self.ui.intensFilt
		Filt = active.text().upper().strip().replace(" ","").replace('+',',').split(',')
		check = []
		if len(Filt)>=1:
			for j in Filt:
				#print(j)
				check.append(j.encode('utf-8') in filtBaseNames)
		else:
			Filt = ['1']
			check = [1.]
		#print(check)
		check = sp.multiply.reduce(check)
		#print(check)

		if check:
			M = self.parent().resFilters(Filt)
		self.filters = M
		print('filters:',  self.filters)
	
	def recalcResult(self):
		self.applyFilt()
		print(self.filters)
		self.result = self.K / sp.pi / self.Ai2 / 1000. * self.filters
		self.ui.result.setText(str(self.result))
		
	def recalcAi2(self):
		z, length, f, Ae = self.getValue(("Z", "length", "F", "R"))
		Ae *= 25*10**-4
		self.Ai2 = 2*Ae**2*((1-z/f)**2 + (z*length*10**-7/pi/Ae**2)**2)/4

		if self.Ai2:
			self.ui.Ai2.setText(str(sqrt(self.Ai2)))
		## парарапаваілваопівлаормидіяваропфіджмиоіжмгіпимжівгпмцзжкамгріважмгп
	
	def getValue(self, names):
		return (getattr(self.ui, i).value() for i in names)
	
		
	def getBackFromQcut(self):
		data= self.qcut.getData()
		self.data[self.activeIndex][0] = data
		
	def plotCurrent(self, index):
		self.activeIndex = index
		self.qcut.show()
		self.qcut.Plot(self.data[index][0])
		
	def recalcCalibr(self):
		
		if len(self.data)>=1:
			X, Y = [], []
			for data in self.data:
				X.append(data[0][:,1].mean())
				Y.append(data[1])
			k = sp.polyfit(X, Y, 1)[0]
			if k:
				self.K = k
				self.ui.calibr.setText(str(k))
		#except: print('Error')
	
	def typeExp(self, index):
		if index == 0:
			self.ui.recalcCalibr.setEnabled(True)
			self.ui.file.setEnabled(True)
			self.ui.namesList.setEnabled(True)
			
		if index == 1:
			self.ui.recalcCalibr.setEnabled(False)
			self.ui.file.setEnabled(False)
			self.ui.namesList.setEnabled(False)
			self.K = self.kPICODict[self.parent().LENGTH]
			self.ui.calibr.setText(str(self.K))
	
	def getFilesForRecalc(self):
		Path = self.fileDialog.getOpenFileNames(self,'Open File', self.Root)
		self.ui.applyFilesList.clear()
		if len(Path)>=1:
			for i in Path:
				name = os.path.basename(i).split('.')[0]
				self.ui.applyFilesList.addItem(name)
				self.outFilesNames.append(i)
	
	def applyForFiles(self):
		xc = self.ui.xColumn.value()
		for i in self.outFilesNames:
			t = True
			try:
				data = sp.loadtxt(i)
			except (ValueError, IOError, IndexError):
				t = False
			if t:
				data[:, xc] *= float(self.ui.result.text())
				path,  name = os.path.split(i)
				suffix = ''
				if self.ui.saveSuffix.text():
					suffix = "_" + self.ui.saveSuffix.text()
				name = name.split('.')[0] +\
					suffix + '.' + name.split('.')[1]
				sp.savetxt(os.path.join(path, name),  data)	
				print(name)

	def getCalibrFile(self):
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
				self.ui.recalcAi2.setEnabled(True)
	
	def updateActiveDataList(self):
		l = self.parent().nameBox.count()
		self.ui.activeDataType.clear()
		for i in range(l):
			self.ui.activeDataType.addItem(self.parent().nameBox.itemText(i))
			
	def uiConnect(self):
		#self.ui.buttonBox.rejected.connect(self.close)
		
		self.ui.recalcAi2.clicked.connect(self.recalcAi2)
		self.ui.hideWindow.clicked.connect(self.close)
		self.ui.file.clicked.connect(self.getCalibrFile)
		self.qcut.dataChanged.connect(self.getBackFromQcut)
		self.ui.recalcCalibr.clicked.connect(self.recalcCalibr)
		self.ui.namesList.currentRowChanged[int].connect(self.plotCurrent)
		#self.parent().settings.ui.typeexp.currentIndexChanged[int].connect(self.typeExp)
		self.ui.recalcResult.clicked.connect(self.recalcResult)
		
		self.ui.applyForActiveData.clicked.connect(self.applyForActiveData)
		self.ui.getFilesForRecalc.clicked.connect(self.getFilesForRecalc)
		self.ui.applyForFiles.clicked.connect(self.applyForFiles)
