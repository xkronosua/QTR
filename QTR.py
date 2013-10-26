#!/usr/bin/python3
# _*_ coding: utf-8 _*_
import sys, os, signal, random

from PySide import QtGui, QtCore, QtUiTools

import scipy as sp


import scipy.interpolate as interp
from scipy.optimize import leastsq
import scipy.optimize as optimize
from numpy.lib.stride_tricks import as_strided

#import shelve
#from glue_designer2 import  DesignerMainWindow
#from ui.Ui_form import Ui_MainWindow
#from intens import IntensDialog
#from settings import SettingsDialog
#from createProject import ProjectDialog
#import bspline
#from console import scriptDialog
import warnings

from mplwidget import MplWidget
from scipy.signal import filtfilt, butter  #lfilter, lfilter_zi
import json
import traceback
import datetime







def loadUi(uifilename, parent=None):
	loader = QtUiTools.QUiLoader(parent)
	ui = loader.load(uifilename)
	return ui

def swap(x,y):	return y,x 	#переворот точок для обрізки

#We're going to weight with a Gaussian function
def gaussian(x,amp=1,mean=0,sigma=1):
	return amp*sp.exp(-(x-mean)**2/(2*sigma**2))

def moving_average(x,y,step_size=.1,bin_size=1):
	bin_centers  = sp.arange(x.min(), x.max()-0.5*step_size,step_size)+0.5*step_size
	bin_avg = sp.zeros(len(bin_centers))

	eq = sp.poly1d(sp.polyfit(x,y,6))
	for index in range(0,len(bin_centers)):
		bin_center = bin_centers[index]
		
		items_in_bin = y[(x>(bin_center-bin_size*0.5) ) & (x<(bin_center+bin_size*0.5))]
		if len(items_in_bin)==0:
			bin_avg[index] = None
		else:
			bin_avg[index] = sp.mean(items_in_bin)
	bin_centers = bin_centers[-sp.isnan(bin_avg)]
	bin_avg = bin_avg[-sp.isnan(bin_avg)]
	
	return (bin_centers,bin_avg)

def weighted_moving_average(x,y,step_size=0.05,width=1):
	bin_centers  = sp.arange(x.min(),x.max()-0.5*step_size,step_size)+0.5*step_size
	bin_avg = sp.zeros(len(bin_centers))
	
	for index in range(0,len(bin_centers)):
		bin_center = bin_centers[index]
		weights = gaussian(x,mean=bin_center,sigma=width)
		bin_avg[index] = sp.average(y,weights=weights)

	return (bin_centers,bin_avg)


# Масив даних, що буде містити дані, їх масштаби, кольори та коментарії
class dataArray(sp.ndarray):

	def __new__(cls, input_array, scales=[0,0], comments="", color='b', x_start=None, x_end=None):
		# Input array is an already formed ndarray instan ce
		# We first cast to be our class type
		obj = sp.asarray(input_array).view(cls)
		# add the new attribute to the created instance
		obj.comments = comments
		obj.scaleX = scales[0]
		obj.scaleY = scales[1]
		obj.scales = scales
		obj.color = color
		obj.x_end = x_end
		obj.x_start = x_start

		# Finally, we must return the newly created object:
		return obj

	def clone(self, array):
		'''передача атрибутів'''
		return dataArray(array, color=self.color, scales=self.getScale(),
			comments=self.comments, x_start=self.x_start, x_end=self.x_end)

	def __array_finalize__(self, obj):
		# see InfoArray.__array_finalize__ for comments
		
		if obj is None: return
		self.comments = getattr(obj, 'comments', None)
		self.scaleX= getattr(obj, 'scaleX', None)
		self.scaleY = getattr(obj, 'scaleY', None)
		self.scales = getattr(obj, 'scales', None)
		self.color = getattr(obj, 'color', None)
		self.x_start = getattr(obj, 'x_start', None)
		self.x_end = getattr(obj, 'x_end', None)
		
	def getScale(self): return [self.scaleX, self.scaleY]

	

class QTR(QtGui.QMainWindow):
	try:
		MAIN_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
	except NameError:
		MAIN_DIRECTORY = os.path.dirname(os.path.abspath("QTR"))
	
	filtersPath = os.path.join(MAIN_DIRECTORY,"filters.dict")	 # База фільтрів
	filtersDict = json.load(open(filtersPath))				# Словник фільтрів
	confDict = dict(
		Scale=[0, 0], 
		Reset=False,
		Undo=False,
		LENGTH="1064",				# Довжина хвилі за замовчуванням
		showTmp=False,		# Показувати проміжні  побудови
		tableEditedName=None,
		nameEditLock=True,
		currentName=None,
		autoscale=True,
		kPICODict={'1064':5.03*10**-3, '532':0.002,"633" : 0.003}
		)
	#  mpl
	x1,x2,x3,x4,y1,y2,y3,y4 = (0.,0.,0.,0.,0.,0.,0.,0.)

	def __init__(self, parent=None):
		super(QTR, self).__init__(parent)
		

		self.PATH = self.MAIN_DIRECTORY
		self.ui = loadUi(os.path.join(self.MAIN_DIRECTORY, 'mainwindow.ui'), self)

		self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)

		## mpl
		self.lock = 0
		self.issecond = 0
		self.background = None

		self.mpl = MplWidget(self)
		self.ui.mplWidget.addWidget(self.mpl)
		self.ui.addToolBar(self.mpl.ntb)
		
		##< mpl

		
		## випадаючий список варіантів нормування
		self.ui.toolBarGraph.addAction(self.ui.menu_norm.menuAction())
		self.ui.menu_norm.menuAction().setIcon(
			QtGui.QIcon(os.path.join(self.MAIN_DIRECTORY,'./buttons/norm_On.png')))
		self.ui.menu_norm.setActiveAction(self.ui.norm_FirstPoint)

		## випадаючий список назв даних
		self.nameBox = QtGui.QComboBox()
		self.nameBox.setObjectName('fastDataComboBox')
		self.ui.statusbar.addPermanentWidget(self.nameBox)
		
		## фільтри
		fDict = self.filtersDict[self.ui.filtWaveLENGTH.currentText()]
		for i in fDict:
			self.ui.filtersList.addItem(i+"\t\t"+str(fDict[i]))
		
		self.filtLineEdit = 'X'
		

		self.ui.stackedWidget.setCurrentWidget(self.getUi('page_Data'))
		self.uiConnect()

		self.plt, = self.mpl.canvas.ax.plot([], [], '.')

		#########################################################################
		data = sp.rand(5,2)
		data = data[data[:,0].argsort()]
		#basename = "tmp_data~"
		#suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
		#filename = "_".join([basename, suffix]) # e.g. 'mylogfile_120508_171442'
		self.data = {}	#shelve.open(filename)
		#self.addNewData(name='new', data=data, color='red')
		

		self.fileDialog = QtGui.QFileDialog(self)
		
		#self.ui.stackedWidget.setCurrentIndex(6)
		self.ui.show()
		
		
		self.ui.filePath.setText('./data/Cr2.dat')
	#############################################################################
	############	 Вкладка  "дані"	#########################################
	#############################################################################

	def namesBoxLinks(self):
		'''Прив’язка перимикання між випадаючим списком імен та таблицею даних'''
		current = self.nameBox.currentIndex()
		print(current)
		self.ui.namesTable.setCurrentCell(current, 0)
		
	def syncData(self):
		#  TODO: придумати щось оригінальніше 
		pass#print(self.data)
		#self.data.sync()

	def plotData(self, name):
		'''Побудова даних:)'''
		self.update_graph()
		#array = self.getData(name)
		#self.plt.set_data(array[:,0], array[:,1])
		#self.plt.set_color(array.color)
		#self.mpl.canvas.ax.relim()
		#self.mpl.canvas.ax.autoscale_view()
		#self.update_graph()
		#self.mpl.canvas.draw()
		
	def saveData(self):
		'''Збереження активного масиву до текстового файлу'''
		if self.sender().objectName() == 'actionSaveData':
			self.ui.stackedWidget.setCurrentWidget(self.getUi('page_Data'))
		Name = self.currentName()
		data,_ = self.getData(Name)
		if not data is None:
			filename = self.fileDialog.getSaveFileName(self,
				'Save File', os.path.join(self.PATH, Name))[0]
			print(filename)
			if filename:
				delimiter = self.getDelimiter()
				print(delimiter)

				if filename.split('.')[-1] == 'npy':
					sp.save(str(filename), data)
				else:
					sp.savetxt(str(filename), data, delimiter=delimiter)
				

	def addNewData(self, name='new', data=sp.empty((0,1)),
		color='red', scales=[0,0], comments="", xc='-', yc='-'):
		'''Додавання нових даних в таблицю та в словник'''

		while name in self.data.keys():
			name_s = name.split('_')
			if name_s[-1].isnumeric():
				name = "_".join(name_s[:-1]) + "_" + str(int(name_s[-1]) + 1)
			else:
				name+="_0"
		
		D = dataArray(data, scales=scales, comments=comments, color=color)
		self.data[name] = (D,)

		self.syncData()
		print(self.data.keys())

		counter = self.ui.namesTable.rowCount()
		counter += 1
		self.ui.namesTable.setRowCount(counter)
		self.ui.namesTable.setColumnCount(3)
		try:
			self.ui.namesTable.itemChanged.disconnect(self.editTableItemName)
		except RuntimeError:
			traceback.print_exc()

		newItem0 = QtGui.QTableWidgetItem()
		newItem0.setText(name)
		newItem0.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable)
		self.ui.namesTable.setItem(counter - 1, 0, newItem0)
		newItem1 = QtGui.QTableWidgetItem()


		newItem1.setText("(" + str(xc) + ',' + str(yc) + ")")
		newItem1.setFlags(QtCore.Qt.ItemIsEnabled)
		self.ui.namesTable.setItem(counter - 1, 1, newItem1)
		
		newItem2 = QtGui.QTableWidgetItem()
		#col = QtGui.QColorDialog.getColor()
		newItem2.setBackground(QtGui.QColor(color))

		newItem2.setFlags(QtCore.Qt.ItemIsEnabled)
		self.ui.namesTable.setItem(counter - 1, 2, newItem2)
		

		self.ui.namesTable.itemChanged.connect(self.editTableItemName)
		
		self.ui.namesTable.clearSelection()
		self.ui.namesTable.setCurrentCell(counter - 1,0)
		try:
			self.nameBox.currentIndexChanged.disconnect(self.namesBoxLinks)
		except RuntimeError:
			traceback.print_exc()

		self.nameBox.clear()
		for i in range(counter):
			text = self.ui.namesTable.item(i, 0).text()
			self.nameBox.addItem(text)
		current = self.ui.namesTable.currentRow()
		
		self.nameBox.currentIndexChanged.connect(self.namesBoxLinks)
		self.nameBox.setCurrentIndex(current)
		
		if hasattr(self, 'intensDialog'):
				self.intensDialog.updateActiveDataList()
		self.ui.namesTable.resizeColumnsToContents()
		#self.plotData(name)
		return name

	def getData(self, name=None):
		'''Доступ до активних даних'''
		
		if name is None:
			name = self.currentName()
		
		if name in self.data:
			data = self.data[name][0].copy()
			if self.ui.actionProcessView.isChecked():
				xl = self.mpl.canvas.ax.get_xlim()
				x_start = sp.where(data[:,0] >= xl[0])[0][0]
				x_end = sp.where(data[:,0] <= xl[1])[0][-1]

				subregion = data[x_start:x_end]
				subregion.x_start = x_start
				subregion.x_end = x_end
				return (subregion, name)
			else:
				return (data, name)

		else: raise KeyError
		
	def getNamesList(self):
		'''Доступ до списку імен даних'''
		counter = self.ui.namesTable.rowCount()
		names = []
		for i in range(counter):
			names.append(self.ui.namesTable.item(i, 0).text())
		return names

	def updateData(self, name, data=None, color=None,
		scales=None, comments=None, x_start=None, x_end=None, showTmp=True):
		'''Оновлення існуючих даних та їх атрибутів'''
		prev_data = []
		if name in self.data:
			prev_data = self.data[name][0].copy()
		else: raise KeyError

		if data is None and color is None and scales is None and comments is None:
			print("foo")
		else:
			if data is None:
				data = prev_data
			if color is None:
				color = prev_data.color
			if scales is None:
				scales = prev_data.getScale()
			if comments is None:
				comments = prev_data.comments
		
		update_subregion = True	
		
		if hasattr(data, 'x_start') and x_start is None:
			if not data.x_start is None:
				x_start = data.x_start

		if hasattr(data, 'x_end') and x_end is None:
			if not data.x_end is None:
				x_end = data.x_end
		
		#print(data, prev_data, prev_data.x_start, prev_data.x_end)
		
		if x_start is None and x_end is None:
			update_subregion = False
		elif x_start is None:
			x_start = sp.where(data[:,0] == data[:,0].min())[0][0]
		elif x_end is None:
			x_end = sp.where(data[:,0] == data[:,0].max())[0][0]
		else:
			pass

		
		#print(x_start,x_end)
		if update_subregion:
			if x_start >= x_end:
				warnings.warn("\nupdate_subregion:\tx_start >= x_end", UserWarning)
			#print(prev_data[:x_start], data, prev_data[x_end:], prev_data, data.x_end, data.x_start)

			data = sp.vstack((prev_data[:x_start], data, prev_data[x_end:]))
		else:
			pass

		self.data[name] = (dataArray(data, scales=scales, comments=comments, color=color), self.data[name])
		
		self.ui.Undo.setEnabled(True)
		self.ui.Reset.setEnabled(True)
		
		self.syncData()
		self.update_graph(name, showTmp=showTmp)

	def undoData(self, name=None):
		if name is None:
			name = self.currentName()
		if len(self.data[name]) == 2:
			self.data[name] = self.data[name][1]
			if len(self.data[name]) != 2:
				self.ui.Undo.setEnabled(False)
				self.ui.Reset.setEnabled(False)
		self.plotData(name)
		
	def resetData(self, name=None):
		if name is None:
			name = self.currentName()
		if len(self.data[name]) == 2:
			data = self.data[name]
			while len(data) == 2:
				if len(data[1]) == 2:
					data = data[1]
				else: break
			self.data[name] = data[1]
		self.plotData(name)

		self.ui.Reset.setEnabled(False)
		self.ui.Undo.setEnabled(False)

	def removeAllData(self, name=None):
		if name is None:
			for i in self.data.keys():
				del self.data[i]
		else:
			if name in self.data:
				del self.data[name]

	def getFilePath(self):
		'''Вибір файлу для завантаження'''
		path = str(self.fileDialog.getOpenFileName(self,'Open File', self.PATH)[0])
		print(path)
		if path:
			self.PATH = os.path.dirname(path)
			#self.Path[active[0]] = path
			self.ui.filePath.setText(path)
		self.ui.addToTable.setEnabled(os.path.exists(self.ui.filePath.text()))
	
	def getDelimiter(self):
		'''Вибір розділювачів даних'''
		delimiters = {
			'space': ' ',
			'space space': '  ', 
			'tab': '\t', 
			',': ',', 
			'.': '.', 
			';': ';',
			'none (*.npy)': None
			}
		return delimiters[self.ui.delimiter.currentText()]

	def pathTextChanged(self, text):
		"""Якщо поле з шляхом до файлу для завантаження було змінене"""
		state = os.path.exists(self.ui.filePath.text())

		if not state:
			self.sender().setStyleSheet('background-color: magenta;')
		else:
			self.sender().setStyleSheet('background-color: inherited;')
		self.ui.addToTable.setEnabled(state)

	def addData(self):
		'''Завантаження даних з файлів'''
		
		path = self.ui.filePath.text()
		print(path)
		if os.path.exists(path):
			#try:
				MAIN_DIRECTORY = os.path.dirname(path)
				
				attr = self.getUi([i + 'Column' for i in ('x', 'y', 'm')])
				xc = attr[0].value()
				yc = attr[1].value()
				mc = attr[2].value()
				try:
					x, y, m = [], [], []
					if path.split('.')[-1] == 'npy':
						data = sp.load(path)
						x, y, m = data[:,xc], data[:, yc], data[:,mc]
					else:
						x, y, m = sp.loadtxt(path, delimiter=self.getDelimiter(), usecols=(xc,yc,mc), unpack=True, comments="#")
				except:
					traceback.print_exc()
				
				if self.ui.isNormColumn.isChecked():
					XY = sp.array( [x/m, y/m]).T
				else:
					XY = sp.array( [x, y]).T
				#XY = XY[XY[:,0] != 0]
				#XY = XY[XY[:,1] != 0]
				p = -1
				pathIndex = self.ui.selectPartOfData.currentIndex()
				if pathIndex == 1:
					p = sp.where( XY[:,0] == XY[:,0].max())[0][0]
					XY = XY[:p,:]
				elif pathIndex == 2:
					p = sp.where( XY[:,0] == XY[:,0].max())[0][0]
					XY = XY[p:,:]
				else:
					pass
				XY = XY[sp.argsort(XY[:,0])]
				if self.getUi('shift0').isChecked():
					y0 = sp.poly1d(sp.polyfit(XY[:,0], XY[:,1], 1))(0.)
					XY[:,1] -= y0


				
				Name = os.path.splitext(os.path.basename(path))[0]
				
				color = 'blue'
				state = 1 #---------------------------------------------
				
				if state:
					self.addNewData(data=XY, scales=[0, 0], name=Name, color=color, xc=xc, yc=yc)
			#except (ValueError, IOError, IndexError):
			#	self.mprint("loadData: readError")
		else:  self.mprint('loadData: pathError')

	def updateNamesTable(self):
		c = self.ui.namesTable.rowCount()
		self.nameBox.clear()
		for i in range(c):
			self.nameBox.addItem(self.ui.namesTable.item(i, 0).text())
		if hasattr(self, 'intensDialog'):
			self.intensDialog.updateActiveDataList()

	def editTableItemName(self, item):
		
		if item.column() == 0 and self.confDict['tableEditedName'] and not self.confDict['nameEditLock']\
				and item.text() not in self.data.keys():

			#print(self.confDict['tableEditedName'], item.text(), self.data.keys())
			self.data[item.text()] = self.data[self.confDict['tableEditedName']]
			del self.data[self.confDict['tableEditedName']]
			self.ui.namesTable.item(item.row(),0).setText(item.text())
			print(self.confDict['tableEditedName'],"\t-->\t", item.text(),"\t|\t", self.data.keys())
			self.confDict['nameEditLock'] = True
			print(dir(item))
			self.updateNamesTable()
			self.ui.namesTable.resizeColumnsToContents()

		
		else:
			if self.confDict['tableEditedName']:
				self.ui.namesTable.itemChanged.disconnect(self.editTableItemName)
				item.setText(self.confDict['tableEditedName'])
				self.ui.namesTable.itemChanged.connect(self.editTableItemName)

	def editTableItem(self, clicked):
		item0 = self.ui.namesTable.item(clicked.row(), 0)
		
		if clicked.column() == 0:
			self.confDict['tableEditedName'] = item0.text()
			self.confDict["nameEditLock"] = False
			
		elif clicked.column() == 2:
			col = QtGui.QColorDialog.getColor()
			self.ui.namesTable.item(clicked.row(), 2).setBackground(col)

			self.updateData(item0.text(), color=col.name())

	def currentName(self):
		'''Назва активних даних'''
		row = self.ui.namesTable.currentRow()
		if self.ui.namesTable.item(row, 0) is None:
			print('Name: None')
			return
		else:
			return self.ui.namesTable.item(row, 0).text()

	def tableItemChanged(self, item):
		if not item is None:
			Name = item.text()
			if Name in self.data.keys():
				state = False
				if len(self.data[Name])==2:
					state = True
				
				self.plotData(Name)
				
				self.setPrevScale()
				self.ui.Reset.setEnabled(state)
				self.ui.Undo.setEnabled(state)

			# поновлення швидкого списку даних
			self.nameBox.currentIndexChanged.disconnect(self.namesBoxLinks)
			self.nameBox.setCurrentIndex(item.row())
			self.nameBox.currentIndexChanged.connect(self.namesBoxLinks)
			if hasattr(self, 'intensDialog'):
				self.intensDialog.updateActiveDataList()

	def rowMoveInTable(self):
		action = self.sender().objectName()[7:]
		if action == "Down":
			row = self.ui.namesTable.currentRow()
			column = self.ui.namesTable.currentColumn();
			if row < self.ui.namesTable.rowCount()-1:
				self.ui.namesTable.insertRow(row+2)
				for i in range(self.ui.namesTable.columnCount()):
					self.ui.namesTable.setItem(row+2,i,self.ui.namesTable.takeItem(row,i))
					self.ui.namesTable.setCurrentCell(row+2,column)
				self.ui.namesTable.removeRow(row)		


		if action == "Up":	
			row = self.ui.namesTable.currentRow()
			column = self.ui.namesTable.currentColumn();
			if row > 0:
				self.ui.namesTable.insertRow(row-1)
				for i in range(self.ui.namesTable.columnCount()):
				   self.ui.namesTable.setItem(row-1,i,self.ui.namesTable.takeItem(row+1,i))
				   self.ui.namesTable.setCurrentCell(row-1,column)
				self.ui.namesTable.removeRow(row+1)
		self.updateNamesTable()

	def deleteFromTable(self):
		#try:
		
		selected = self.ui.namesTable.selectionModel().selectedIndexes()
		rows = []
		names = []
		for i in selected:
			rows.append(i.row())
			name = self.ui.namesTable.item(i.row(), 0).text()
			#del self.data[name]
			print(self.data.keys(), name)
			names.append(name)
		print(rows)
		rows.sort()
		for i in rows[::-1]:
			print(i)
			self.ui.namesTable.removeRow(i)
			self.nameBox.removeItem(i)

		print("-"*10)
		for i in names:
			print(self.data.keys(), i)
			del self.data[i]
		print(self.data.keys())
		self.updateNamesTable()

	def multiPlot(self):
		selected = self.ui.namesTable.selectionModel().selectedIndexes()
		lines = []
		for i in selected:
			name = self.ui.namesTable.item(i.row(), 0).text()
			data,_ = self.getData(name)
			lines.append(self.mpl.canvas.ax.plot(data[:,0], data[:,1], ".", color=data.color, alpha=0.5)[0])
		self.mpl.canvas.draw()
		for i in lines:
			self.mpl.canvas.ax.lines.remove(i)
	

	###########################################################################
	######################	Нормування даних	###############################
	###########################################################################

	def norm_FirstPoint(self):
		''' Нормування на першу точку '''

		Name = self.currentName()
		data,_ = self.getData(Name)
		if not data is None:
			try:
				data[:, 1] /= data[0, 1]
				self.updateData(name=Name, data=data)
				xl = self.mpl.canvas.ax.get_xlim()
				l1, = self.mpl.canvas.ax.plot(xl, [1]*2, 'r')
				l2, = self.mpl.canvas.ax.plot(data[0, 0], 1, 'ro', markersize=6)
				self.mpl.canvas.draw()
				self.mpl.canvas.ax.lines.remove(l1)
				self.mpl.canvas.ax.lines.remove(l2)
			except:
				traceback.print_exc() 
				
	def norm_Max(self):
		''' Нормування на максимум '''
		Name = self.currentName()
		data,_ = self.getData(Name)
		if not data is None:
			try:
				data[:, 1] /= data[:, 1].max()
				self.updateData(name=Name, data=data)
			except:
				traceback.print_exc() 

	def norm_Shift0X(self):
		''' Центрування по X'''
		Name = self.currentName()
		data,_ = self.getData(Name)
		if not data is None:
			try:
				data[:,0]=data[:,0]-data[data[:,1]==data[:,1].max(),0]

				self.updateData(name=Name, data=data)
			except:
				traceback.print_exc() 

	def norm_Shift0(self):
		''' Видалення фонової компоненти '''
		Name = self.currentName()
		data,_ = self.getData(Name)
		if not data is None:
			try:
				p = int(len(data)/4)
				y0 = sp.poly1d(sp.polyfit(data[:p,0], data[:p,1], 1))(0.)
				data[:,1] -= y0
				#data[:, 1] /= data[:, 1].max()
				self.updateData(name=Name, data=data)
			except:
				traceback.print_exc() 
	
	def norm_Point(self, state):
		''' Нормувати на вказану точку '''

		def on_press(event):
			''' Отримання координат точки для нормування на точку '''
			if not event.xdata is None and not event.ydata is None:
				Name = self.currentName()
				data,_ = self.getData(Name)
				if not data is None:
					data[:, 1] /= event.ydata
					self.updateData(Name, data=data)
					xl = self.mpl.canvas.ax.get_xlim()
					self.mpl.canvas.ax.plot(xl, [1]*2, 'r')
					self.mpl.canvas.ax.plot(event.xdata, 1, 'ro', markersize=6)
					self.mpl.canvas.draw()
					self.mpl.canvas.mpl_disconnect(self.cidpress)
					self.mpl.canvas.mpl_disconnect(self.cidmotion)
					self.ui.norm_Point.setChecked(False)
					
		def on_motion(event):
			if not event.xdata is None and not event.ydata is None:
				xl = self.mpl.canvas.ax.get_xlim() 
				yl = self.mpl.canvas.ax.get_ylim()
				self.mpl.canvas.ax.figure.canvas.restore_region(self.background)
				self.mpl.canvas.ax.set_xlim(xl)
				self.mpl.canvas.ax.set_ylim(yl)
				

				self.line.set_xdata(xl)
				self.line.set_ydata([event.ydata]*2)
	
				# redraw artist
				self.mpl.canvas.ax.draw_artist(self.line)
				self.mpl.canvas.ax.figure.canvas.blit(self.mpl.canvas.ax.bbox)
				
		if state:
			self.cidpress = self.mpl.canvas.mpl_connect(
					'button_press_event', on_press)
			self.cidmotion = self.mpl.canvas.mpl_connect(
					'motion_notify_event', on_motion)

		else:
			try:
				self.mpl.canvas.mpl_disconnect(self.cidpress)
				self.mpl.canvas.mpl_disconnect(self.cidmotion)
				self.update_graph()
			except:
				traceback.print_exc()

	###########################################################################
	######################	Масштаби 	###############################
	###########################################################################		
	# Повернути масштаб при поверненні в історії
	def setPrevScale(self):
		actions = ('actionY_X', 'actionX_Log10', 'actionY_Log10' )
		
		data, Name = self.getData()
		if not data is None:
			scale = data.getScale()
			ui_actions = self.getUi(actions)
			for t in ui_actions:
				t.toggled[bool].disconnect(self.setNewScale)
				t.setEnabled(False)
				t.setChecked(False)
			if scale[1] == 2:
				ui_actions[0].setChecked(True)
			else:
				for i, j in enumerate((False, scale[0], scale[1])):
					ui_actions[i].setChecked(j)
			ui_actions[0].setEnabled( not (ui_actions[1].isChecked() or ui_actions[2].isChecked()))
			ui_actions[1].setEnabled( not ui_actions[0].isChecked() )
			ui_actions[2].setEnabled( not ui_actions[0].isChecked() )
			
			for t in ui_actions:
				t.toggled[bool].connect(self.setNewScale)
		
	# Змінити масштаб на новий
	def setNewScale(self, state):
		actions = ('actionY_X', 'actionX_Log10', 'actionY_Log10' )
		senderName = self.sender().objectName()
		Name = self.currentName()
			
		data,_ = self.getData(Name)
		if not data is None:
			Scale = data.getScale()
			#ui_obj = self.getUi([t + i for i in Names])
			ui_actions = self.getUi(actions)
			if senderName == actions[0]:
				#ui_obj = getattr(self.ui, t + "LogScale")
				if state:
					Scale[1] = 2
					data = data[data[:, 0] != 0]
					data[:,1] = data[:,1] / data[:,0]
				else:
					Scale[1] = 0
					data[:,1] = data[:,1] * data[:,0]
				for i in ui_actions[1:]:
					i.setEnabled(not ui_actions[0].isChecked())
					
			else:
				index = bool(senderName[6] != "X")
				#ui_obj = getattr(self.ui, t + Names[0])
				if Scale[index] != state:
					if state == 1:
						data = data[data[:, index] > 0]
						data[:,index] = sp.log10(data[:,index])
					else:
						data[:,index] = sp.power(10.,data[:,index])
					Scale[index] = int(state)
					#ui_obj[0].setEnabled(##	not (ui_obj[1].isChecked() or ui_obj[2].isChecked()))
					ui_actions[0].setEnabled(
						not (ui_actions[1].isChecked() or ui_actions[2].isChecked()) )
			
			
			self.updateData(name=Name, data=data, scales=Scale, showTmp=False)

	###########################################################################
	######################	Графічні методи 	###############################
	###########################################################################
	def Rescale(self):
		
		try:
			XY,_ = self.getData()
			xMargin = abs( XY[:,0].max() - XY[:,0].min() ) * 0.05
			yMargin =  abs( XY[:,1].max() - XY[:,1].min() ) * 0.05
			
			self.mpl.canvas.ax.set_xlim( (XY[:,0].min() - xMargin,\
				XY[:,0].max() + xMargin) )
			self.mpl.canvas.ax.set_ylim( (XY[:,1].min() - yMargin,\
				XY[:,1].max() + yMargin) )
		except:
			traceback.print_exc()

	def update_graph(self, name=None, showTmp=True):
		"""Updates the graph with new X and Y"""
		# TODO: rewrite this routine, to get better performance
		
	
		#self.background = \
		#	self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
		# save current plot variables
		if name is None:
			data, name = self.getData()

		else:
			data,_ = self.getData(name)

		if self.confDict['autoscale'] and len(data)>2:
			self.Rescale()
		
		if self.background != None:
			# save initial x and y limits
			self.xl = self.mpl.canvas.ax.get_xlim()
			self.yl = self.mpl.canvas.ax.get_ylim()
		
		# clear the axes
		self.mpl.canvas.ax.clear()
		# plot graph
		self.mpl.canvas.ax.axis[:].invert_ticklabel_direction()
		#self.mpl.canvas.ax.set_xticks(self.mpl.canvas.ax.get_xticks()[1:-1])

		
		if self.confDict['showTmp'] and len(self.data[name]) == 2 and showTmp:
			#print(data.color)
			prev_data = self.data[name][1][0]
			c = QtGui.QColor(data.color).getRgb()
			new_color = QtGui.QColor(255 - c[0], 255 - c[1], 255 - c[2], 255)
			self.plt_tmp, = self.mpl.canvas.ax.plot(prev_data[:, 0],\
				prev_data[:, 1], color = new_color.name(), marker='+', linestyle='None', markersize=4, alpha=0.35)
		
		self.plt, = self.mpl.canvas.ax.plot(data[:, 0],\
			data[:, 1],color = data.color, marker='o', linestyle='None', markersize=5, alpha=0.9)
		
		
		if not hasattr(self, 'line'):
			# creating line
			self.line, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'g--', animated=True)
		if not hasattr(self, 'points'):
			# creating points
			self.points, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'mo', animated=True, markersize=3)
		if not hasattr(self.ui, 'rectab') :								
			# creating rectangle
			self.rect, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'm--', animated=True)
			self.rectab, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--', animated=True)
			self.rectbc, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--', animated=True)
			self.rectcd, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--', animated=True)
			self.rectda, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--', animated=True)
		# TODO: create a circle
		# enable grid
		self.mpl.canvas.ax.grid(True)
		
		
		if self.background != None:
			# set x and y limits
			self.mpl.canvas.ax.set_xlim(self.xl)
			self.mpl.canvas.ax.set_ylim(self.yl)
		
		
		#self.set_x_log(self.ui.xLogScale.isChecked(), redraw = False)
		#self.set_y_log(self.ui.yLogScale.isChecked(), redraw = False)
		# force an image redraw
		self.mpl.canvas.draw()
		
		# copy background
		self.background = \
			self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
		# make edit buttons enabled
		
		self.ui.mplactionCut_by_line.setEnabled(self.background != None)
		self.ui.mplactionCut_by_rect.setEnabled(self.background != None)


		#self.mpl.canvas.ax.relim()
		#self.mpl.canvas.ax.autoscale_view()
		
		#if sp.shape(data) != self.tempShape :
		#	self.tempShape = sp.shape(data)
		#	self.data_signal.emit()

	def draw_line(self):
		self.mpl.canvas.ax.figure.canvas.restore_region(self.background)
		self.line.set_xdata([self.x1, self.x2])
		self.line.set_ydata([self.y1, self.y2])
		# redraw artist
		self.mpl.canvas.ax.draw_artist(self.line)
		self.mpl.canvas.ax.figure.canvas.blit(self.mpl.canvas.ax.bbox)

	def draw_rect(self):
		self.mpl.canvas.ax.figure.canvas.restore_region(self.background)
		self.rect.set_xdata([self.x1, self.x1, self.x2, self.x2, self.x1])
		self.rect.set_ydata([self.y1, self.y2, self.y2, self.y1, self.y1])
		
		# redraw artists
		self.mpl.canvas.ax.draw_artist(self.rect)

		self.mpl.canvas.ax.figure.canvas.blit(self.mpl.canvas.ax.bbox)

	############################## Line #######################################
	
	def cut_line(self,state):
		"""start cut the line"""
		if state:
			
			#self.sdata = data.copy()
			self.cidpress = self.mpl.canvas.mpl_connect(
					'button_press_event', self.on_press)
			self.cidrelease = self.mpl.canvas.mpl_connect(
					'button_release_event', self.on_release)
		else:
			self.issecond = 0
			self.mpl.canvas.mpl_disconnect(self.cidpress)
			self.mpl.canvas.mpl_disconnect(self.cidrelease)
			if hasattr(self,'cidmotion'):
				self.mpl.canvas.mpl_disconnect(self.cidmotion)
			self.update_graph()
		self.ui.mplactionCut_by_rect.setEnabled(not state)
		self.ui.stackedWidget.setEnabled(not state)
			
	def on_press(self, event):
		"""on button press event for line
		"""
		if not event.xdata is None and not event.ydata is None:
			# copy background
			name = self.currentName()

			data,_ = self.getData(name)
			self.background = \
				self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
			if self.issecond == 0:
				self.x1 = event.xdata
				self.y1 = event.ydata
				self.cidmotion = self.mpl.canvas.mpl_connect('motion_notify_event', self.on_motion)
				return
	
			if self.issecond == 1 :
				self.x3 = event.xdata
				self.y3 = event.ydata
				# point swap
				if self.x1 >= self.x2:
					self.x1, self.x2 = swap(self.x1, self.x2)
					self.y1, self.y2 = swap(self.y1, self.y2)
				try:
					y = ((self.y2 - self.y1) / (self.x2 - self.x1)) * \
						(self.x3 - self.x2) + self.y2
					X = data[:,0]
					Y = data[:,1]
					yy =  ((self.y2 - self.y1) / (self.x2 - self.x1)) * \
							(X - self.x2) + self.y2
				except:
					y = 0.
				if self.y3 >= y:
					# up cut
					w = (X>=self.x1) * (X<=self.x2) * (Y>=yy) 
					data = data[~w,:]

				else:
					#down cut					
					w = (X>=self.x1) * (X<=self.x2) * (Y<=yy) 
					data = data[~w,:]
				self.updateData(name, data=data)
				
				
				self.ui.mplactionCut_by_line.setChecked(False)
		else:
			
			self.ui.mplactionCut_by_line.setChecked(False)
			return

	def on_motion(self, event):
		'''on motion we will move the rect if the mouse is over us'''
		if not event.xdata is None and not event.ydata is None:
			self.x2 = event.xdata
			self.y2 = event.ydata
			self.draw_line()
		else:
			self.ui.mplactionCut_by_line.setChecked(False)

	def on_release(self, event):
		'''on release we reset the press data'''
		if not event.xdata is None and not event.ydata is None:
			self.x2 = event.xdata
			self.y2 = event.ydata
			self.issecond = 1
			self.draw_line()
			if self.x1 and self.x2 and self.y1 and self.y2:
				#self.mpl.canvas.mpl_disconnect(self.cidpress)
				self.mpl.canvas.mpl_disconnect(self.cidmotion)
				self.mpl.canvas.mpl_disconnect(self.cidrelease)
			else:
				self.mpl.canvas.mpl_disconnect(self.cidpress)
		else:
			self.ui.mplactionCut_by_line.setChecked(False)
		
	############################### Rect ####################################
	def cut_rect(self, state):
		if state:
			"""start to cut the rect"""
			#self.sdata = data.copy()
			self.cidpress = self.mpl.canvas.mpl_connect(
					'button_press_event', self.on_press2)
			self.cidrelease = self.mpl.canvas.mpl_connect(
					'button_release_event', self.on_release2)
		else:
			self.issecond = 0
			self.mpl.canvas.mpl_disconnect(self.cidpress)
			self.mpl.canvas.mpl_disconnect(self.cidrelease)
			if hasattr(self,'cidmotion'):
				self.mpl.canvas.mpl_disconnect(self.cidmotion)
			self.update_graph()
		self.ui.mplactionCut_by_line.setEnabled(not state)
		self.ui.stackedWidget.setEnabled(not state)
		
	def on_press2(self, event):
		"""on button press event for rectangle
		"""
		if not event.xdata is None and not event.ydata is None:
			# copy background
			name = self.currentName()
			data,_ = self.getData(name)
			self.background = \
				self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
			# first press
			if self.issecond == 0:
				self.x1 = event.xdata
				self.y1 = event.ydata
				
				self.cidmotion = self.mpl.canvas.mpl_connect('motion_notify_event', self.on_motion2)
				return
			# second press
			if self.issecond == 1 :
				self.x3 = event.xdata
				self.y3 = event.ydata
				# point swap
				if self.x1 > self.x2:
					self.x1, self.x2 = swap(self.x1, self.x2)
					if self.y1 < self.y2:
						self.y1, self.y2 = swap(self.y1, self.y2)
					else:
						delta = self.y1 - self.y2
						self.y1 -= delta
						self.y2 += delta
				else:
					if self.y1 < self.y2:
						delta = self.y2 - self.y1
						self.y1 += delta
						self.y2 -= delta
					else:
						pass
				X = data[:,0]
				Y = data[:,1]
				w = (X>=self.x1) * (X<=self.x2) * (Y<=self.y1) * (Y>=self.y2)
				if self.y3 <= self.y1 and self.y3 >= self.y2 and self.x3 >= self.x1 and self.x3 <= self.x2 :
					# in cut
					data = data[~w,:]
				else:
					#out cut
					data = data[w,:]

				self.updateData(name, data=data)
				self.ui.mplactionCut_by_rect.setChecked(False)

		else:
			self.ui.mplactionCut_by_rect.setChecked(False)
		return

	def on_motion2(self, event):
		'''on motion we will move the rect if the mouse is over us'''
		if not event.xdata is None and not event.ydata is None:
			self.x2 = event.xdata
			self.y2 = event.ydata
			self.draw_rect()
		else:
			self.ui.mplactionCut_by_rect.setChecked(False)

	def on_release2(self, event):
		'''on release we reset the press data'''
		if not event.xdata is None and not event.ydata is None:
			self.x2 = event.xdata
			self.y2 = event.ydata
			self.issecond = 1
			self.draw_rect()
			if self.x1 and self.x2 and self.y1 and self.y2:
				#self.mpl.canvas.mpl_disconnect(self.cidpress)
				self.mpl.canvas.mpl_disconnect(self.cidmotion)
				self.mpl.canvas.mpl_disconnect(self.cidrelease)
			else:
				self.mpl.canvas.mpl_disconnect(self.cidpress)
		else:
			self.ui.mplactionCut_by_rect.setChecked(False)

	def set_autoScale(self, flag):
		"""change Y|X autoscale"""
		if flag:
			self.confDict['autoscale'] = True
			self.update_graph()
			#self.Rescale()
		else :
			self.confDict['autoscale'] = False

	def processView(self, state):
		if state:
			self.ui.autoScale.setChecked(False)

	def plotTmp(self, state):
		'''Проміжні побудови'''
		self.confDict['showTmp'] = state
		if not state: self.update_graph()

	
	###########################################################################################################################
	######################	Фільтри, сплайни...	###############################################################################
	'''---------------------------------------------------------------------------------------------------------------------'''
	###########################################################################################################################
	
	#  page_FiltFilt
	def filtFilt(self):
		data, Name = self.getData()
		if not data is None:
			p = self.ui.FiltFiltP.value()
			k = self.ui.FiltFiltK.value()
			b, a = butter(k, p)
			X = data[:,0]
			Y = data[:,1] 
			if self.ui.FiltFiltY.isChecked():
				Y = filtfilt(b, a, Y)
			if self.ui.FiltFiltX.isChecked():
				X = filtfilt(b, a, X)
			
			self.updateData(name=Name, data=data.clone(sp.array([X, Y]).T))


	#  page_PolyFit
	def polyApprox(self):
		''' Апроксимація поліномом n-го степ. '''
		data, Name = self.getData()
		X, Y = data[:, 0], data[:, 1]
		step = self.getUi('ApproxStep').value()
		M = self.getUi('ApproxM').value()
		
		
		EQ = sp.poly1d( sp.polyfit(X, Y, M) )
		xnew = sp.arange(X.min(), X.max(), step)
		ynew = EQ( xnew )
		
		

		self.updateData(name=Name, data=data.clone(sp.array([xnew, ynew]).T))
		
		if self.confDict['showTmp']:
			#self.mpl.canvas.ax.plot(x,  y, '.m',  alpha=0.2,  zorder=1)
			xl = self.mpl.canvas.ax.get_xlim()
			yl = self.mpl.canvas.ax.get_ylim()
			
			text = ''
			for j, i in enumerate(EQ):
				text+="+"*(i>0) + str(i)+" x^{" + str(M-j) +"}"
			text = "$" + text[(EQ[0]>0):] + "$"
			print(text)
			
			#self.mpl.canvas.ax.text(xl[0], yl[0], text, fontsize=15, color='orange')
			
			#self.mpl.canvas.draw()

	#  page_B_spline
	def connectAutoB_sS(self, state):
		'''Оновлення коеф. згладжування'''
		spins = ['S', 'Step', 'K']
		for j in spins:
			if state:
				self.getUi('B_spline' + j).valueChanged.connect(
								self.AutoB_splineS)
			else:
				self.getUi('B_spline' + j).valueChanged.disconnect(
								self.AutoB_splineS)

	def AutoB_splineS(self, state=None, param=0.98):
		'''Штучний підбір коефіцієнтів для b-сплайн інтерполяції'''
		spins = ('S',  'Step', 'K')
		state = self.getUi('AutoB_splineS').isChecked()
		active = self.getUi(['B_spline' + i for i in spins])
		
		data, Name = self.getData()
		
		active[0].setEnabled(not state)
		m = len(data)
		active[0].setValue(sp.std(data[:,1])**2*(m - sp.sqrt(m*2)))
		'''
		if state:
			
			y = data[:,1]
			x = data[:,0]
			EQ = sp.poly1d( sp.polyfit(x, y, 3) )
			poly_Y = EQ( x )
			Y = y - poly_Y
			Step = float(active[1].value())
			K = float(active[2].value())

			try:
				print(str((1+Step/K**3)*param))
				active[0].setValue(sp.std(Y)**2*len(y)*(1+Step/K**2)*param)
			except:
				traceback.print_exc()
		'''
		
	def B_spline(self):
		'''інтерполяція b-сплайном'''
		spins = ['B_spline' + i for i in ('Step', 'S', "K")]
		step, sm, km = (i.value() for i in self.getUi(spins))
		XY, Name = self.getData()
		X, Y = XY[:,0], XY[:,1]
		xi = sp.arange(X.min(), X.max(),step)

		
		if self.getUi('B_splineSMin').isChecked():
			i = 0
			j = 0
			for i in sp.exp(sp.arange(sm,0,-sm/2000)/sm*sp.exp(1))*sm/sp.exp(1):
				if sp.isnan(interp.UnivariateSpline(X,Y, s=i, k=int(km)).get_coeffs()).sum() >0:
					break
				else:
					j = i
			sm = j

			self.getUi('B_splineS').setValue(sm)

		uspline = interp.UnivariateSpline(X,Y, s=sm, k=int(km))
		
		data = sp.array([xi, uspline(xi)]).T
		data = XY.clone(data)
		'''
		# Оптимізація
		if self.getUi('B_splineLeastsq').isChecked():
			residuals = lambda  coeffs, xy: (xy[:,1] - sp.poly1d(coeffs)(xy[:,0]))
			uCoeffs = uspline.get_coeffs()
			plsq = leastsq(residuals, uCoeffs, args=XY)
			
			data = sp.array([xi, sp.poly1d(plsq[0])(xi)]).T
		'''
		self.updateData(name=Name, data=data)
		
	
	def poly_cut(self, data=None, N=10, m=4,
		p=0.80, AC=False,  discrete=False):
		'''	Обрізка вздовж кривої апроксиміції поліномом.
		m		-	степінь полінома
		p		-	відсоток від максимального викиду
		N		-	кількість вузлів
		AC	-	обробити Все, зробити Зріз, Зшити
		'''
		data, name = self.getData()

		X, Y = data[:,0], data[:,1]

		params = self.getUi(['Poly' + i for i in 'NPM'])
		step_size, p, m = (i.value() for i in params)

		discrete = self.ui.poly_cutDiscrete.isChecked()


		#bin_centers  = sp.arange(X.min(), X.max()-0.5*step_size,step_size)+0.5*step_size
# 		bin_size = step_size*1.05
# 		X_, Y_ = weighted_moving_average(X, Y, step_size, bin_size)
# 		#sp.poly1d( sp.polyfit(X, Y, m) )
# 		
# 		x_new = sp.hstack((X[:5], X_, X[-5:]))
# 		y_new = sp.hstack((Y[:5], Y_, Y[-5:]))
# 		y_new = y_new[x_new.argsort()]
# 		x_new = x_new[x_new.argsort()]
# 		
#		y_wma = interp.interp1d(x_new, y_new)(X)
		x_new = X #sp.arange(X.min(), X.max(), step_size)
		y_new = sp.poly1d(sp.polyfit(X, Y, m))(X)
		y_wma = y_new
		y_wma = abs(Y - y_wma)
		X_new, Y_new, Y_tmp = [],[],[]
		if not discrete:
			w = y_wma < y_wma.max()*p
			X_new = X[w]
			Y_new = Y[w]
			
		else:
			bin_centers  = sp.arange(X.min(), X.max()-0.5*step_size,step_size)+0.5*step_size
			bin_size = step_size
			bin_avg = sp.zeros(len(bin_centers))

			for index in range(0,len(bin_centers)):
				bin_center = bin_centers[index]
				W = (X>(bin_center-bin_size*0.5) ) & (X<(bin_center+bin_size*0.5))
				x_tmp = X[W]
				y_tmp = y_wma[W]
				if W.sum()<=1: continue
				else:
					
					w = y_tmp < y_tmp.max()*p
					X_new.append(x_tmp[w])
					Y_new.append(Y[W][w])
		
		X_new = sp.hstack(X_new)
		Y_new = sp.hstack(Y_new)
		out = sp.array([X_new, Y_new]).T
		Y_tmp = interp.interp1d(x_new, y_new)(X_new)
		
		out = out[out[:,0].argsort()]
		out = data.clone(out)
		
		self.updateData(name, data=out)
		if self.confDict['showTmp']:

			#Y_tmp = sp.hstack(Y_tmp).T
			print(sp.shape(Y_tmp), sp.shape(out))
			#Y_tmp = Y_tmp[out[:,0].argsort()]
			self.mpl.canvas.ax.plot(out[:,0], Y_tmp, '-r')
			self.mpl.canvas.draw()

	def movingAverage(self):
		'''Ковзаюче усереднення'''
		data, name = self.getData()
		step = self.getUi('AverageStep').value()
		width = self.getUi('maWidth').value()
		
		x, y = moving_average(data[:,0], data[:,1],step,width)
		new_data = data.clone(sp.array([x,y]).T)
		self.updateData(name, data=new_data)
		#if self.confDict['showTmp']:
		#	self.mpl.canvas.ax.plot(x, y, '-r')
		#	self.mpl.canvas.draw()
	
	def setFilters(self):
		'''Посадка  на фільтри'''
		
		active = self.getUi([i+'Filt' for i in ['X', 'Y']])
		res_text = self.getUi(['res'+i+'Filt' for i in ['X', 'Y']])
		
		filtBaseNames = list(self.filtersDict[self.ui.filtWaveLENGTH.currentText()].keys())
		
		M = [1., 1.]
		for i, j in enumerate(active):
			M[i] = self.filtCalc(j.text())
			print(M[i])

		if M[0]!=1. or M[1]!=1.:
			#for i in [0,1]:	self.filtList[Name][i] = M[i]
			data, name = self.getData()
			if not data is None:
				print(M)
				for i in [0,1]:
					if not M[i] is None:
						data[:,i] = data[:,i] / M[i]  #self.filtList[index][0]
						res_text[i].setText(str(M[i]))

				#data[:,1] = data[:,1]/M[1]  #self.filtList[index][1]
				self.updateData(name, data=data)
			#self.mprint("Filters [X,Y]: %s" % str(self.filtList[index]))

	def setFiltLineEdit(self):
		self.filtLineEdit = self.sender().objectName()[0]
	
	def updateFiltersList(self, index):
		''' Оновлення списку фільтрів для даної довжини хвилі'''
		fDict = self.filtersDict[self.ui.filtWaveLENGTH.currentText()]
		self.ui.filtersList.clear()
		for i in fDict:
			self.ui.filtersList.addItem(i+"\t\t"+str(fDict[i]))
		
		
	def addFiltInEditLine(self, item):

		currentEditLine = self.getUi(self.filtLineEdit + "Filt")
		currentEditLine.setText(currentEditLine.text() + "," + item.text().split('\t')[0])
	
	def filtCalc(self, filters, waveLength=None):
		"""Обрахунок пропускання для послідовності фільтрів"""
		filtTable = self.filtersDict
		if waveLength is None:
			waveLength = self.ui.filtWaveLENGTH.currentText()
			
		if filters:
			if not filtTable is None:
				filters = filters.replace(' ', '').replace('+', ',').replace(';', ',')
				res = 1.
				try:
					res = sp.multiply.reduce( [ filtTable[waveLength][i.upper()] for i in filters.split(",")] )
				except KeyError:
					traceback.print_exc()
					return 1.
				return res
			else:
				return 1.
		else:
			return 1.

	def normDataAdd(self):
		counter = self.ui.normTable.rowCount()
		self.ui.normTable.setRowCount(counter + 1)
		for i in range(5):
			newItem = QtGui.QTableWidgetItem()
			self.ui.normTable.setItem(counter, i, newItem)
	
		combo1 = QtGui.QComboBox()
		combo2 = QtGui.QComboBox()
		names = self.getNamesList()
		for i in names:
			combo1.addItem(i)
			combo2.addItem(i)
			
		self.ui.normTable.setCellWidget(counter, 0, combo1)
		self.ui.normTable.setCellWidget(counter, 1, combo2)
		self.ui.normTable.item(counter, 2).setText('Нормувати >')

		self.ui.normTable.item(counter, 4).setText('-')
		
		self.ui.normTable.item(counter, 2).setFlags(QtCore.Qt.ItemIsEnabled)
		self.ui.normTable.item(counter, 4).setFlags(QtCore.Qt.ItemIsEnabled)
		
		#normButton = QtGui.QToolButton()
		#self.ui.normTable.setCellWidget(counter, 2, normButton)
		#saveButton = QtGui.QToolButton()
		#self.ui.normTable.setCellWidget(counter, 4, saveButton)
		
		
	def normDataRemove(self):
			#try:
		
		selected = self.ui.normTable.selectionModel().selectedIndexes()
		rows = []
		for i in selected:
			rows.append(i.row())
			#name = self.ui.normTable.item(i.row(), 0).text()
			del self.dataDict[name]
			#print(self.dataDict.keys(), name)
		rows.sort()
		for i in rows[::-1]:
			self.ui.normTable.removeRow(i)
			self.nameBox.removeItem(i)
		

	def normTableItemClicked(self, item):
		if item.column() == 2:
			name1 = self.ui.normTable.cellWidget(item.row(), 0).currentText()
			name2 = self.ui.normTable.cellWidget(item.row(), 1).currentText()
			name3 = name1 + '_' + name2
			cData, _ = self.getData(name2)
			sData, _ = self.getData(name1)
			x, y = [], []
			if cData.scales == [0,0] and sData.scales == [0,0]:
			
			#if self.ui.rButton.isEnabled():
				x = sData[:,0]
				window = (x>=cData[:,0].min())*(x<=cData[:,0].max())

				x = x[window]
				y = sData[:,1]
				y = y[window]
				cY_tmp = sp.interpolate.interp1d(cData[:,0], cData[:,1],self.ui.normEvalType.currentText().lower())(x)
				x = x[cY_tmp != 0]
				y = y[cY_tmp != 0]
				cY_tmp = cY_tmp[cY_tmp != 0]
				y = y/ cY_tmp
				print(sp.shape(x),sp.shape(y))
				outName = self.addNewData(name = name3, data=sp.array([x,y]).T)

				self.ui.normTable.item(item.row(), 3).setText(outName)
				self.ui.normTable.item(item.row(), 4).setText('Ok')
			else: print('ResEval: interpTypeError')
	
	## Інтенсивність
	def recalcAi2(self):
		'''Перерахунок радіусу пучка'''
		z, f, Ae = self.getValue(("Z", "F", "R"))
		length = float(self.ui.intensWaveLENGTH.currentText())
		Ae *= 25*10**-4
		try:
			Ai2 = 2*Ae**2*((1-z/f)**2 + (z*length*10**-7/sp.pi/Ae**2)**2)/4
			self.ui.Ai2.setText(str(sp.sqrt(Ai2)))
		except:
			traceback.print_exc()
			self.ui.Ai2.setText(str(sqrt(Ai2)))
	
	def recalcIntensResult(self):
		'''Перерахунок на інтенсивність'''
		filt = self.filtCalc(self.ui.intensFilt.text(), waveLength=self.ui.intensWaveLENGTH.currentText())
		try:
			
			result = float(eval(self.ui.calibr.text().replace("^","**"))) / float(self.ui.Ai2.text())**2 /  filt
			self.ui.intensResult.setText(str(round(result,9)))
			data, Name = self.getData()
			data[:, 0] *= float(self.ui.intensResult.text())
			self.updateData(name=Name, data=data)
			
		except:
			traceback.print_exc()

			
	#=============================================================================
	def getUi(self, attrNames):
		if type(attrNames) in (type([]), type(())):
			return tuple(getattr(self.ui, i) for i in attrNames)
		else:
			return getattr(self.ui, attrNames)
	
	def getValue(self, names):
		return (getattr(self.ui, i).value() for i in names)
	
	def setToolsLayer(self):
		name = self.sender().objectName().split('action')[1]
		self.ui.stackedWidget.setCurrentWidget(self.getUi('page_'+name))
		if name == 'B_spline':
			self.AutoB_splineS()

	def uiConnect(self):
		'''Пов’язвння сигналів з слотами'''
		
		##############  Filters	###############################################
		self.ui.FiltOk.clicked.connect(self.setFilters)
		
		##############  ReHi3	  ###############################################
		#self.ui.reHi3_ok.clicked.connect(self.recalcReHi3)
		##############  NormData   ###############################################
		self.ui.normDataAdd.clicked.connect(self.normDataAdd)
		self.ui.normDataRemove.clicked.connect(self.normDataRemove)
		self.ui.normTable.itemClicked.connect(self.normTableItemClicked)
		
		##############  PolyFit	###############################################
		self.ui.PolyApprox.clicked.connect(self.polyApprox)
		
		##############  PolyCut	###############################################
		self.ui.PolyOk.clicked.connect(self.poly_cut)
		
		##############  B_spline   ###############################################
		self.ui.B_splineOk.clicked.connect(self.B_spline)
		self.ui.AutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		self.ui.AutoB_splineS.toggled[bool].connect(self.connectAutoB_sS)
		
		##############  Average	###############################################
		self.ui.AverageOk.clicked.connect(self.movingAverage)
		##############  FiltFilt   ###############################################
		self.ui.FiltFiltOk.clicked.connect(self.filtFilt)
		
		##############  page_Data  ###############################################
		self.ui.selectFile.clicked.connect(self.getFilePath)
		self.ui.filePath.textChanged.connect(self.pathTextChanged)
		self.ui.addToTable.clicked.connect(self.addData)
		self.ui.namesTable.doubleClicked.connect(self.editTableItem)
		self.ui.rowMoveUp.clicked.connect(self.rowMoveInTable)
		self.ui.rowMoveDown.clicked.connect(self.rowMoveInTable)
		self.ui.deleteData.clicked.connect(self.deleteFromTable)
		self.ui.isNormColumn.toggled.connect(self.ui.mColumn.setEnabled)
		self.ui.namesTable.currentItemChanged.connect(self.tableItemChanged)
		
		self.nameBox.currentIndexChanged.connect(self.namesBoxLinks)
		self.ui.namesTable.itemChanged.connect(self.editTableItemName)
		self.ui.saveData.clicked.connect(self.saveData)
		self.ui.actionSaveData.triggered.connect(self.saveData)
		self.ui.multiPlot.clicked.connect(self.multiPlot)

		##########################################################################
		

		
		self.ui.Undo.triggered.connect(self.undoData)
		self.ui.Reset.triggered.connect(self.resetData)
		self.ui.Undo.triggered.connect(self.setPrevScale)
		self.ui.Reset.triggered.connect(self.setPrevScale)


		self.ui.tmpShow.toggled[bool].connect(self.plotTmp)
		self.ui.autoScale.toggled[bool].connect(self.set_autoScale)

		#self.ui.processView.toggled[bool].connect(self.processView)
		self.ui.actionProcessView.toggled[bool].connect(self.processView)
	
		## norm
		self.ui.norm_Max.triggered.connect(self.norm_Max)
		self.ui.norm_Point.toggled[bool].connect(self.norm_Point)
		self.ui.norm_FirstPoint.triggered.connect(self.norm_FirstPoint)
		self.ui.norm_Shift0.triggered.connect(self.norm_Shift0)
		self.ui.norm_Shift0X.triggered.connect(self.norm_Shift0X)
		
		
		#self.ui.settings.triggered.connect(self.settings.show)
		# Масштабування
		self.ui.actionY_X.toggled[bool].connect(self.setNewScale)
		##self.ui.checkY_X.toggled[bool].connect(self.ui.actionY_X.toggle)
		self.ui.actionY_Log10.toggled[bool].connect(self.setNewScale)
		self.ui.actionX_Log10.toggled[bool].connect(self.setNewScale)


		## Фільтри
		self.ui.filtWaveLENGTH.currentIndexChanged.connect(self.updateFiltersList)
		self.ui.filtersList.itemDoubleClicked.connect(self.addFiltInEditLine)
		self.ui.XFilt.textEdited.connect(self.setFiltLineEdit)
		self.ui.YFilt.textEdited.connect(self.setFiltLineEdit)
		
		##	mpl
		self.ui.mplactionCut_by_line.toggled[bool].connect(self.cut_line)
		self.ui.mplactionCut_by_rect.toggled[bool].connect(self.cut_rect)
		
		## Інтенсивність
		self.ui.recalcAi2.clicked.connect(self.recalcAi2)
		self.ui.recalcIntensResult.clicked.connect(self.recalcIntensResult)
		

		'''
		#self.ui.rYInPercents.toggled[bool].connect(self.rYInPercents)
		self.ui.movePoint.triggered.connect(self.movePoint)
		self.ui.Close.triggered.connect(self.close)
		#self.close.connect(self.closeEvent)
		#self.ui.LENGTH.currentIndexChanged[str].connect(self.setLength)
		#___________________________		_____________________
		
		
		#+++++++++++++++++++  Intensity	 ++++++++++++++++++++++++++++++++++++++
		self.ui.recalcIntens.triggered[bool].connect(self.recalcIntens)

		self.ui.console.triggered.connect(self.console.show)
		
		####################  calibrDialog  ######################################
		#self.calibrDialog.ui.ok.clicked.connect(self.getCalibr)
		#self.ui.recalcCalibr.clicked.connect(self.recalcCalibr)
		'''
		####################  mainToggle	######################################
		self.ui.actionPolyCut.triggered.connect(self.setToolsLayer)
		self.ui.actionPolyFit.triggered.connect(self.setToolsLayer)
		self.ui.actionB_spline.triggered.connect(self.setToolsLayer)
		self.ui.actionAverage.triggered.connect(self.setToolsLayer)
		self.ui.actionFiltFilt.triggered.connect(self.setToolsLayer)
		self.ui.actionData.triggered.connect(self.setToolsLayer)
		self.ui.actionNormData.triggered.connect(self.setToolsLayer)
		self.ui.actionReHi3.triggered.connect(self.setToolsLayer)
		self.ui.actionFilters.triggered.connect(self.setToolsLayer)
		self.ui.actionIntens.triggered.connect(self.setToolsLayer)
		



def main():



	signal.signal(signal.SIGINT, signal.SIG_DFL) # Застосування Ctrl+C в терміналі

	app = QtGui.QApplication(sys.argv)
	win = QTR()
	

	sys.exit(app.exec_())
	

			
if __name__ == "__main__":
	main()
