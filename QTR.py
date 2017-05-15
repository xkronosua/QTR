#!/usr/bin/python3
# _*_ coding: utf-8 _*_
from __future__ import print_function


# This must be the first statement before other statements.
# You may only put a quoted or triple quoted string, 
# Python comments or blank lines before the __future__ line.


from optparse import OptionParser

parser = OptionParser()
parser.add_option("--qt4", dest="qt4", action="store_true", help="for pyqt4", default=False)
parser.add_option("--qt5", dest="qt5", action="store_true", help="for pyqt5", default=True)
(ScriptOptions, ScriptArgs) = parser.parse_args()
print(ScriptOptions, ScriptArgs)
import sys, os, signal, random, glob
#import pdb
if ScriptOptions.qt4:
	print("Qt4")
	from PyQt4 import QtGui, QtCore, uic, QtGui as QtWidgets # QtUiTools
	from PyQt4.QtCore import QSettings, qDebug
else:
	print("Qt5")
	from PyQt5 import QtGui, QtCore, uic, QtWidgets # QtUiTools
	from PyQt5.QtCore import QSettings, qDebug


import scipy as sp

import scipy.interpolate as interp
from scipy.optimize import leastsq
import scipy.optimize as optimize
from numpy.lib.stride_tricks import as_strided
from scipy.signal import medfilt
from scipy.signal import argrelextrema

# import shelve
# from glue_designer2 import  DesignerMainWindow
# from ui.Ui_form import Ui_MainWindow
# from intens import IntensDialog
# from settings import SettingsDialog
# from createProject import ProjectDialog
# import bspline
# from console import scriptDialog
import warnings
from functools import wraps

from mplwidget import MplWidget, SpanSelector
import matplotlib.pyplot as plt
from scipy.signal import filtfilt, butter  # lfilter, lfilter_zi
import json
import traceback
from datetime import datetime
import h5py
import shutil

import cmath
from calc_n2_newForVG import calcReChi3
from calc_all_victor_1 import calcImChi3
from calc_n2_new_cw532_1 import calcReChi3CW

from guisave import *

import logging
from pprint import pformat


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
import pandas

filtersDict_indicatrix = {"532": {1:1,'1': 1, "OP06": 1/10**0.6, "OP09": 1/10**0.9, "OP18": 1/10**1.8}}
def convertRawFilter(filt,waveLenght="532"):
	filt = filt.upper()
	filters = filt.replace(' ','').replace('\n','').replace('\t','').split(',')
	conv = [filtersDict_indicatrix[waveLenght][i] for i in filters]
	res = 1
	for i in conv:
		res*=i
	return res

def isIndicatrixData(filename):
	testStr = "#ch1\tch2\tch3\tch4\tN\tlastUpdate_time\tlaser_dt\tangle"
	with open(filename, 'r') as fobj:
		for line in fobj:
			if line.startswith('#ch1'):
				return True
				break

def indicatrixRaw2Data(filename,convertRawFilter_=convertRawFilter):
	
	header = []
	comments = []
	#with open('filters.dict') as f:
	#	filtersDict = json.load(f)	
	
	filtersRaw = []
	WAVELENGHT = "532"
	
	with open(filename, 'r') as fobj:
		# takewhile returns an iterator over all the lines 
		# that start with the comment string
		for n,line in enumerate(fobj):
			if line.startswith('#'):
				#print(n, line)
				comments.append([n,line.split(';')])
			if line.startswith('#Filter:'):
				print(n, line,	line.split(':')[-1], WAVELENGHT, convertRawFilter_(line.split(':')[-1], WAVELENGHT))
				filtersRaw.append([n, convertRawFilter_(line.split(':')[-1], WAVELENGHT)])
			if line.startswith('#ch'):
				header = line[1:-1].split('\t')
		#headiter = takewhile(lambda s: ss(s), fobj)
		# you may want to process the headers differently, 
		# but here we just convert it to a list
		#header = list(headiter)
	df = pandas.read_csv(filename, comment='#',sep='\t',names = header)
	df['filter'] = pandas.np.ones(len(df))
	k = pandas.np.where(df['N']==1)[0]

	for i in range(len(k)-1):
		df['filter'][k[i]:k[i+1]] = filtersRaw[i][1]

	df['scat'] = df['ch3']/df['filter']
	df = df[df['scat']>=0]

	return df.loc[:,['angle','scat']].values
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%



def _print(*args, **kwargs):
	"""My custom print() function."""
	# Adding new arguments to the print function signature 
	# is probably a bad idea.
	# Instead consider testing if custom argument keywords
	# are present in kwargs
	#print(kwargs)
	if 'type' in kwargs:
		if kwargs['type'] == "error":
			logging.error((args))
	else:
		logging.debug((args))
	#__builtins__.print('My overridden print() function!')
	#return __builtins__.print(*args, **kwargs)

#def print(*args):
#	logging.debug((args))

def loadUi(uifilename, parent=None):
	# loader = QtUiTools.QUiLoader(parent)
	#try:
	#	ui = __import__(uifilename.split('.')[-2].replace('/','').split('\\')[-1].split('/')[-1])
		
	#except:
	ui = uic.loadUi(uifilename)  # loader.load(uifilename)
	#	traceback.print_exc()
	return ui


def swap(x, y):	return y, x  # переворот точок для обрізки


# We're going to weight with a Gaussian function
def gaussian(x, amp=1, mean=0, sigma=1):
	return amp * sp.exp(-(x - mean) ** 2 / (2 * sigma ** 2))


def moving_average(x, y, step_size=.1, bin_size=1):
	bin_centers = sp.arange(x.min(), x.max() - 0.5 * step_size, step_size) + 0.5 * step_size
	bin_avg = sp.zeros(len(bin_centers))
	bin_err = sp.zeros(len(bin_centers))

	eq = sp.poly1d(sp.polyfit(x, y, 8))
	for index in range(0, len(bin_centers)):
		bin_center = bin_centers[index]

		items_in_bin = y[(x > (bin_center - bin_size * 0.5)) & (x < (bin_center + bin_size * 0.5))]
		if len(items_in_bin) == 0:
			bin_avg[index] = None
			bin_err[index] = None
		else:
			bin_avg[index] = sp.mean(items_in_bin)
			bin_err[index] = sp.std(items_in_bin)
	bin_centers = bin_centers[-sp.isnan(bin_avg)]
	bin_avg = bin_avg[-sp.isnan(bin_avg)]
	bin_err = bin_err[-sp.isnan(bin_avg)]

	return (bin_centers, bin_avg, bin_err)


def weighted_moving_average(x, y, step_size=0.05, width=1):
	bin_centers = sp.arange(x.min(), x.max() - 0.5 * step_size, step_size) + 0.5 * step_size
	bin_avg = sp.zeros(len(bin_centers))

	for index in range(0, len(bin_centers)):
		bin_center = bin_centers[index]
		weights = gaussian(x, mean=bin_center, sigma=width)
		bin_avg[index] = sp.average(y, weights=weights)

	return (bin_centers, bin_avg)


# Масив даних, що буде містити дані, їх масштаби, кольори та коментарії
class dataArray(sp.ndarray):
	def __new__(cls, input_array, scales=[0, 0], comments=dict(), color='b', x_start=None, x_end=None, attrs={}):
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
		obj.attrs = attrs
		# Finally, we must return the newly created object:
		return obj

	def clone(self, array):
		'''передача атрибутів'''
		return dataArray(array, color=self.color, scales=self.attrs['scales'],
						 comments=self.comments, x_start=self.x_start, x_end=self.x_end)

	def __array_finalize__(self, obj):
		# see InfoArray.__array_finalize__ for comments

		if obj is None: return
		self.comments = getattr(obj, 'comments', None)
		self.scaleX = getattr(obj, 'scaleX', None)
		self.scaleY = getattr(obj, 'scaleY', None)
		self.scales = getattr(obj, 'scales', None)
		self.color = getattr(obj, 'color', None)
		self.x_start = getattr(obj, 'x_start', None)
		self.x_end = getattr(obj, 'x_end', None)
		self.attrs = getattr(obj, 'attrs', None)
		

	def getScale(self): return [self.scaleX, self.scaleY]





class QTR(QtWidgets.QMainWindow):
	try:
		MAIN_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
	except NameError:
		MAIN_DIRECTORY = os.path.dirname(os.path.abspath("QTR"))

	filtersPath = os.path.join(MAIN_DIRECTORY, "filters.dict")  # База фільтрів
	filtersDict = json.load(open(filtersPath))  # Словник фільтрів
	confDict = dict(
		Scale=[0, 0],
		Reset=False,
		Undo=False,
		LENGTH="1064",  # Довжина хвилі за замовчуванням
		showTmp=False,  # Показувати проміжні  побудови
		tableEditedName=None,
		nameEditLock=True,
		currentName=None,
		autoscale=True,
		kPICODict={'1064': 5.03 * 10 ** -3, '532': 8.7 * 10 ** -6, "633": 0.003}
	)
	#  mpl
	x1, x2, x3, x4, y1, y2, y3, y4 = (0., 0., 0., 0., 0., 0., 0., 0.)
	projectPath = ""
	projectName = ''
	leastsq_params_ImChi3 = [None, None]
	Settings = None

	def __init__(self, parent=None):
		super(QTR, self).__init__(parent)

		self.settings = QSettings('settings.ini', QSettings.IniFormat)
		self.PATH = self.MAIN_DIRECTORY
		
		#logging.getLogger().setLevel(100)
		self.ui = loadUi(os.path.join(self.MAIN_DIRECTORY, 'mainwindow.ui'), self)
		#logging.getLogger().setLevel(40)
		
		
		if not os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)), "tmp")):
			os.makedirs(os.path.join(os.path.dirname(os.path.realpath(__file__)), "tmp"))
		self.projectName = datetime.now().strftime("%Y%m%d-%H%M%S")
		self.projectPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tmp",
										self.projectName + ".hdf5")
		self.ProjectFile = h5py.File(self.projectPath, 'a')
		self.data = self.ProjectFile.create_group(self.projectName)

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
			QtGui.QIcon(os.path.join(self.MAIN_DIRECTORY, './buttons/norm_On.png')))
		self.ui.menu_norm.setActiveAction(self.ui.norm_FirstPoint)

		self.statusBarMessage = QtWidgets.QLabel()
		self.statusBarMessage.setObjectName('statusBarMessage')
		self.ui.statusbar.addPermanentWidget(self.statusBarMessage)
		## випадаючий список назв даних
		self.nameBox = QtWidgets.QComboBox()
		self.nameBox.setObjectName('fastDataComboBox')
		self.ui.statusbar.addPermanentWidget(self.nameBox)


		## фільтри
		fDict = self.filtersDict[self.ui.filtWaveLENGTH.currentText()]
		for i in fDict:
			self.ui.filtersList.addItem(i + "\t\t" + str(fDict[i]))

		self.filtLineEdit = 'X'

		self.ui.stackedWidget.setCurrentWidget(self.getUi('page_Data'))
		self.fileDialog = QtWidgets.QFileDialog(self)
		self.uiConnect()

		self.plt, = self.mpl.canvas.ax.plot([], [], '.')
		self.points, = self.mpl.canvas.ax.plot([], [], '.')
		self.mplSpan = self.mpl.canvas.ax.axvspan(0, 0, facecolor='g', alpha=0.5)

		#########################################################################
		data = sp.rand(5, 2)
		data = data[data[:, 0].argsort()]
		# basename = "tmp_data~"
		# suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
		# filename = "_".join([basename, suffix]) # e.g. 'mylogfile_120508_171442'
		# self.data = {}	#shelve.open(filename)
		# self.addNewData(name='new', data=data, color='red')

		#self.ui.label.setMouseTracking(True)
		self.ui.installEventFilter(self)
	
		# self.ui.stackedWidget.setCurrentIndex(6)
		self.ui.show()
		
		self.selectedDataDict = dict()
		self.ui.namesTable.setColumnWidth(0, 100);
		self.ui.namesTable.setColumnWidth(1, 40);
		self.ui.namesTable.setColumnWidth(2, 15);


		try:
			#print("loadSettingsFromIni:", self.settings.value('loadSettingsFromIni'))
			#if self.settings.value('loadSettingsFromIni')=='true':
			#logging.getLogger().setLevel(100)
			guirestore(self.ui, self.settings)
			#logging.getLogger().setLevel(40)
			
		except:
			traceback.print_exc()

		if self.ui.filePath.text() == "":
			self.ui.filePath.setText('/home/kronosua/work/QTR/data/Jul2715/nd18.dat')

		QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+H"), self.ui, self.showTmpConfig)
		self.ui.tabifyDockWidget(self.ui.dockWidget_Console, self.ui.DataDock)
	

	#############################################################################g
	############	 Вкладка  "дані"	#########################################
	#############################################################################

	def namesBoxLinks(self):
		'''Прив’язка перимикання між випадаючим списком імен та таблицею даних'''
		current = self.nameBox.currentIndex()
		print(current)
		self.ui.namesTable.setCurrentCell(current, 0)

	def dIndex(self, name):
		return str(max([int(i) for i in self.data[name]['main'].keys()]))

	def getdIndex(self, group):
		return str(max([int(i) for i in group['main'].keys()]))

	def syncData(self):
		#  TODO: придумати щось оригінальніше
		if os.path.exists(self.projectPath):
			self.ProjectFile.flush()
		else:
			open(self.projectPath, 'a').close()
			self.ProjectFile = h5py.File(self.projectPath, 'a')
			self.ProjectFile.copy(self.data, self.data.name)
			self.ProjectFile.flush()
			self.data = self.ProjectFile[self.projectName]
		# data_new = ProjectFile_new.create_group(self.projectName)
		# self.ProjectFile.copy(self.projectName, data_new)
		# print(self.data, data_new)
		# self.ProjectFile = ProjectFile_new
		# self.data = data_new

	# self.data.sync()

	def plotData(self, name):
		'''Побудова даних:)'''
		self.update_graph()

	def showTmpConfig(self):
		self.ui.stackedWidget.setCurrentWidget(self.getUi('page_NormShift'))
	# array = self.getData(name)
	# self.plt.set_data(array[:,0], array[:,1])
	# self.plt.set_color(array.color)
	# self.mpl.canvas.ax.relim()
	# self.mpl.canvas.ax.autoscale_view()
	# self.update_graph()
	# self.mpl.canvas.draw()

	def saveData(self):
		'''Збереження активного масиву до текстового файлу'''
		if self.sender().objectName() == 'actionSaveData':
			self.ui.stackedWidget.setCurrentWidget(self.getUi('page_Data'))
		Name = self.currentName()
		data, _ = self.getData(Name)
		if not data is None:
			filename = ""
			if ScriptOptions.qt4:
				filename = self.fileDialog.getSaveFileName(self,
														   'Save File',
														   os.path.join(self.PATH, Name))
			else:
				filename = self.fileDialog.getSaveFileName(self,
													   'Save File',
													   os.path.join(self.PATH, Name))   [0] #		!!!! Для PySide

			print(filename)
			if filename:
				self.PATH = os.path.dirname(filename)
				delimiter = self.getDelimiter()
				print(delimiter)

				if filename.split('.')[-1] == 'npy':
					sp.save(str(filename), data)
				else:
					sp.savetxt(str(filename), data, delimiter=delimiter)

	def saveAll(self):
		Dir = str(self.fileDialog.getExistingDirectory(self, "Select Directory"))
		print(Dir)
		for i in self.data.keys():
			data, nn = self.getData(i)
			sp.savetxt(os.path.join(Dir, i + ".dat"), data)

	def saveProject(self):
		filename = self.fileDialog.getSaveFileName(self,
												   'Save File',
												   os.path.join(self.PATH, self.ProjectFile.filename))
		if not ScriptOptions.qt4: filename = filename[0]
		print("SaveTo:", filename)

		self.ProjectFile.flush()
		self.ProjectFile.close()
		# del self.ProjectFile

		shutil.copy(self.projectPath, filename)
		self.projectPath = filename
		self.ProjectFile = h5py.File(self.projectPath, 'a')
		for i in self.ProjectFile.keys():
			print(i, self.ProjectFile, '=' * 10)
			for j in self.ProjectFile[i].keys():
				group_item = self.ProjectFile[i][j]
				lastIndex = self.getdIndex(group_item)
				for k in group_item['main'].keys():
					if k != lastIndex:
						del group_item['main'][k]
				#if 'tmp' in group_item.keys():
				#	del group_item['tmp']
		self.ProjectFile.flush()
		self.data = self.ProjectFile[self.projectName]
		print(self.data, [i for i in self.data.items()])

	def openProject(self):

		self.ProjectFile.flush()
		# self.ProjectFile.close()
		filename = self.fileDialog.getOpenFileName(self, 'Open Project', self.PATH)
		if not ScriptOptions.qt4: filename = filename[0]
		
		print("Open:", filename)
		# del self.ProjectFile
		# shutil.move(self.projectPath, filename)
		# self.projectPath = filename
		ProjectFile = h5py.File(filename, 'r')
		for i in ProjectFile.keys():
			print(i, ProjectFile)
			for j in ProjectFile[i].keys():
				newItem = ProjectFile[i][j]
				index = self.getdIndex(newItem)
				newItem = newItem['main'][index]
				print(j, newItem, index)
				self.addNewData(name=j, data=newItem, color=newItem.attrs['color'],
								scales=newItem.attrs['scales'], comments=newItem.attrs)
		# self.data = self.ProjectFile[self.projectName]
		ProjectFile.close()

	def addNewData(self, name='new', data=sp.empty((0, 1)),
				   color='red', scales=[0, 0], comments=dict(), xc='-', yc='-'):
		'''Додавання нових даних в таблицю та в словник'''

		while name in self.data.keys():
			name_s = name.split('_')
			if name_s[-1].isnumeric():
				name = "_".join(name_s[:-1]) + "_" + str(int(name_s[-1]) + 1)
			else:
				name += "_0"

		# if 'shiftForLog10' not in comments.keys():
		#	comments = sp.append('shiftForLog10': None})

		# D = dataArray(data, scales=scales, comments=comments, color=color)
		# self.data[name]['main'] = (D,)
		group = self.data.create_group(name)
		main_subgroup = group.create_group('main')
		tmp_subgroup = group.create_group('tmp')
		tmp_subgroup.create_dataset('activeSubregion', (2, 2), maxshape=(None, 3))
		tmp_subgroup.create_dataset('active', (2, 2), maxshape=(None, 3))
		dset = main_subgroup.create_dataset('0', data=data)

		dset.attrs['scales'] = scales
		dset.attrs['shiftForLog10'] = sp.NaN
		dset.attrs['color'] = color
		dset.attrs['x_start'] = data[:, 0].min()
		dset.attrs['x_end'] = data[:, 0].max()
		dset.attrs['processView'] = False
		for i in comments.keys():
			dset.attrs[i] = comments[i]

		self.ProjectFile.flush()
		# self.syncData()
		# print(self.data.keys())

		counter = self.ui.namesTable.rowCount()
		counter += 1
		self.ui.namesTable.setRowCount(counter)
		self.ui.namesTable.setColumnCount(3)
		try:
			self.ui.namesTable.itemChanged.disconnect(self.editTableItemName)
		except RuntimeError:
			traceback.print_exc()

		newItem0 = QtWidgets.QTableWidgetItem()
		newItem0.setText(name)
		newItem0.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable)
		self.ui.namesTable.setItem(counter - 1, 0, newItem0)
		newItem1 = QtWidgets.QTableWidgetItem()

		newItem1.setText("(" + str(xc) + ',' + str(yc) + ")")
		newItem1.setFlags(QtCore.Qt.ItemIsEnabled)
		self.ui.namesTable.setItem(counter - 1, 1, newItem1)

		newItem2 = QtWidgets.QTableWidgetItem()
		# col = QtWidgets.QColorDialog.getColor()
		newItem2.setBackground(QtGui.QColor(color))

		newItem2.setFlags(QtCore.Qt.ItemIsEnabled)
		self.ui.namesTable.setItem(counter - 1, 2, newItem2)

		self.ui.namesTable.itemChanged.connect(self.editTableItemName)

		self.ui.namesTable.clearSelection()
		self.ui.namesTable.setCurrentCell(counter - 1, 0)
		try:
			self.nameBox.currentIndexChanged.disconnect(self.namesBoxLinks)
		except (RuntimeError, TypeError):
			traceback.print_exc()

		self.nameBox.clear()
		if self.ui.normTable.rowCount() != 0:
			c1 = self.ui.normTable.rowCount()
			c = self.ui.namesTable.rowCount()
			for j in range(c1):
				lastCell0 = self.ui.normTable.cellWidget(j, 0).currentText()
				self.ui.normTable.cellWidget(j, 0).clear()
				lastCell1 = self.ui.normTable.cellWidget(j, 1).currentText()
				self.ui.normTable.cellWidget(j, 1).clear()
				lastInd = [0, 0]
				for i in range(c):
					text = self.ui.namesTable.item(i, 0).text()
					print(text, lastCell0)
					if text == lastCell0:
						lastInd[0] = i
					elif text == lastCell1:
						lastInd[1] = i
					self.ui.normTable.cellWidget(j, 0).addItem(text)
					#self.ui.normTable.cellWidget(j, 1).addItem(text)
					self.ui.normTable.cellWidget(j, 1)
				self.ui.normTable.cellWidget(j, 0).setCurrentIndex(lastInd[0])
				self.ui.normTable.cellWidget(j, 1).setCurrentIndex(lastInd[1])
		for i in range(counter):
			text = self.ui.namesTable.item(i, 0).text()
			self.nameBox.addItem(text)

		current = self.ui.namesTable.currentRow()

		self.nameBox.currentIndexChanged.connect(self.namesBoxLinks)
		self.nameBox.setCurrentIndex(current)

		if hasattr(self, 'intensDialog'):
			self.intensDialog.updateActiveDataList()
		# self.ui.namesTable.resizeColumnsToContents()
		# self.plotData(name)
		return name

	def getData(self, name=None):
		'''Доступ до активних даних'''
		print(name)
		if name is None:
			name = self.currentName()
		print(name)
		data = None
		if name is None:
			return(None, None)

		elif name in self.data:
			prev_data = self.data[name]['main'][self.dIndex(name)]  # self.data[name]['main'][0].copy()

			#data = self.data[name]['main'].create_dataset(str(int(self.dIndex(name))+1), data=prev_data)
			print(prev_data[:,0].min())
			data = self.data[name]['tmp']['active']
			tmp = prev_data.value
			data.resize(len(tmp), 0)
			data.resize(len(tmp.T), 1)
			data[:] = tmp
			print(data.shape)

			for i in prev_data.attrs.keys():
				data.attrs[i] = prev_data.attrs[i]
			if self.ui.actionProcessView.isChecked():
				xl = self.mpl.canvas.ax.get_xlim()
				print(xl,data[:,0].min(), sp.where(data[:, 0] >= xl[0])[0][0],"-"*10)
				x_start = sp.where(data[:, 0] >= xl[0])[0][0]
				x_end = sp.where(data[:, 0] <= xl[1])[0][-1]

				subregion = self.data[name]['tmp']['activeSubregion']
				tmp = data.value[x_start:x_end]
				subregion.resize(len(tmp), 0)
				subregion.resize(len(tmp.T), 1)

				subregion[:] = tmp

				print(subregion, type(subregion), subregion.shape)
				for i in data.attrs.keys():
					subregion.attrs[i] = data.attrs[i]
				prev_data.attrs['x_start'] = x_start
				prev_data.attrs['x_end'] = x_end
				prev_data.attrs['processView'] = True
				subregion.attrs['x_start'] = x_start
				subregion.attrs['x_end'] = x_end
				subregion.attrs['processView'] = True
				data.attrs['x_start'] = x_start
				data.attrs['x_end'] = x_end
				data.attrs['processView'] = True
				return (subregion, name)
			else:
				prev_data.attrs['processView'] = False
				
				data.attrs['processView'] = False
				return (data, name)

		else:
			raise KeyError

	def getNamesList(self):
		'''Доступ до списку імен даних'''
		counter = self.ui.namesTable.rowCount()
		names = []
		for i in range(counter):
			names.append(self.ui.namesTable.item(i, 0).text())
		return names

	def updateData(self, name, data=None, clone=None, color=None,
				   scales=None, comments=None, x_start=sp.nan, x_end=sp.nan, shiftForLog10=None, showTmp=True):
		'''Оновлення існуючих даних та їх атрибутів'''
		prev_data = []
		if name in self.data.keys():
			prev_data = self.data[name]['main'][self.dIndex(name)]  # self.data[name]['main'][0].copy()
		else:
			raise KeyError

		if data is None and color is None and scales is None and comments is None and clone is None:
			print("foo",type="error")
		
		
		if data is None:
			data = prev_data
			print("type(data) == 'NoneType'")
			
		elif type(data) == sp.ndarray:
			print("type(data) == 'numpy.ndarray'")
			
			tdata = self.data[name]['tmp']['active']
			
			tdata.resize(len(data), 0)
			tdata.resize(len(data.T), 1)
			tdata[:] = data
			data = tdata
			for i in prev_data.attrs.keys():
				data.attrs[i] = prev_data.attrs[i]



		elif type(data) == h5py._hl.dataset.Dataset:
			print("type(data) == 'h5py._hl.dataset.Dataset'")
			
		
		else:
			print(type(data))
			
		
		if type(clone) == h5py._hl.dataset.Dataset:
			attrs = dict(clone.attrs)
			for i in attrs.keys():
				data.attrs[i] = attrs[i]

		
		update_subregion = True
		
		try:
			update_subregion = prev_data.attrs['processView']
			print(update_subregion, x_start, x_end, prev_data.attrs['x_start'], data.attrs['x_start'], 'x_start' is data.attrs.keys() , x_start is sp.nan,
								not data.attrs['x_start'] is None)
			if x_start is sp.nan:
				if not data.attrs['x_start'] is sp.nan:
					x_start = data.attrs['x_start']

			if x_end is sp.nan:
				if not data.attrs['x_end'] is sp.nan:
					x_end = data.attrs['x_end']

			#print(x_start, x_end)#, prev_data.attrs['x_start'], prev_data.attrs['x_end'])

			if x_start is sp.nan and x_end is sp.nan:
				update_subregion = False
			else:
				if x_start is sp.nan:
					x_start = sp.where(data[:, 0] == data[:, 0].min())[0][0]
				elif x_end is sp.nan:
					x_end = sp.where(data[:, 0] == data[:, 0].max())[0][0]
				else:
					pass
			
			
			print('Update_subregion: ', update_subregion, x_start, x_end)
			
			if update_subregion:
				if x_start >= x_end:
					warnings.warn("\nupdate_subregion:\tx_start >= x_end", UserWarning)
				# print(prev_data[:x_start], data, prev_data[x_end:], prev_data, data.x_end, data.x_start)
				tdata = sp.vstack((prev_data[0:int(x_start)], data[:, :2], prev_data[int(x_end):-1]))
				data.resize(len(tdata), 0)
				data.resize(len(tdata.T), 1)
				data[:] = tdata
				
			else:
				pass
		except:
				traceback.print_exc()

		new_hist_item = str(1 + int(self.dIndex(name)))
		# print(new_hist_item, [i for i in self.data[name]['main'].keys()], )
		dset = self.data[name]['main'].create_dataset(new_hist_item, data=data)
		#for i in comments.keys():
		#	dset.attrs[i] = comments[i]
		#print('dset.attrs["scales"]', dset.attrs['scales'])
		if scales is None:
			scales = data.attrs['scales']
		dset.attrs['scales'] = scales
		print('dset.attrs["scales"]', dset.attrs['scales'])
		if color is None:
			color = data.attrs['color']
		dset.attrs['color'] = color
		if shiftForLog10 is None:
			shiftForLog10 = data.attrs['shiftForLog10']
		dset.attrs['shiftForLog10'] = shiftForLog10
		if update_subregion:
			try:
				dset.attrs['processView'] = False
				dset.attrs['x_end'] = sp.nan
				dset.attrs['x_start'] = sp.nan
				self.ui.actionProcessView.setChecked(False)
			except:
				traceback.print_exc()
		else:
			
			dset.attrs['x_end'] = dset.value[:,0].max()
			dset.attrs['x_start'] = dset.value[:,0].max()
				
		# self.data[name]['main'] = (dataArray(data, scales=scales, comments=comments, color=color), self.data[name]['main'])

		self.ui.Undo.setEnabled(True)
		self.ui.Reset.setEnabled(True)

		self.syncData()
		print(sys.getsizeof(self.data))
		self.update_graph(name=name,data=dset, showTmp=showTmp)
		self.mprintf(len(dset))

	def dublicateData(self):
		data, name = self.getData()
		print("dublicateData")
		self.addNewData(name=name+"_c", data=data.value)

	def undoData(self, state=None, name=None):
		if name is None:
			name = self.currentName()
		print("UndoData:\t" + name)
		if len(self.data[name]['main']) >= 1:
			del self.data[name]['main'][self.dIndex(name)]
			print("dataLen:",len(self.data[name]['main']), self.data[name]['main'].keys())  # self.data[name]['main'] = self.data[name]['main'][1]
			for i in self.data[name]['main'].keys():
				print(i)
			if len(self.data[name]['main']) == 1:  # len(self.data[name]['main']) != 2:
				self.ui.Undo.setEnabled(False)
				self.ui.Reset.setEnabled(False)
		self.setPrevScale()
		self.plotData(name)

		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(name, self.sender)

	def resetData(self, state=None, name=None):
		if name is None:
			name = self.currentName()

		if len(self.data[name]['main']) > 1:
			for key in self.data[name]['main'].keys():
				if key != '0':
					del self.data[name]['main'][key]
			print("dataLen:",len(self.data[name]['main'])) 
		# if len(self.data[name]['main']) == 2:
		#	data = self.data[name]['main']
		#	while len(data) == 2:
		#		if len(data[1]) == 2:
		#			data = data[1]
		#		else: break
		#	self.data[name]['main'] = data[1]
		self.setPrevScale()
		self.plotData(name)

		self.ui.Reset.setEnabled(False)
		self.ui.Undo.setEnabled(False)

		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(name, self.sender)

	def removeAllData(self, state=None, name=None):
		if name is None:
			# for i in self.data.keys():
			#	del self.data[i]
			for i in self.data.keys():
				del self.data[i]
		else:
			# if name in self.data:
			#	del self.data[name]['main']
			if name in self.data:
				del self.data[name]['main']
		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(name, self.sender)

	def getFilePath(self):
		'''Вибір файлу для завантаження'''
		
		path = self.fileDialog.getOpenFileNames(self, caption="Open Files", directory=self.PATH, )
		print(path)
		if not ScriptOptions.qt4: path = path[0]
		
		if len(path) > 0:
			self.PATH = os.path.dirname(path[0])
			# self.Path[active[0]] = path
			self.ui.filePath.setText(";".join(path))
		self.ui.addToTable.setEnabled(os.path.exists(self.ui.filePath.text().split(';')[0]))

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
		state = os.path.exists(self.ui.filePath.text().split(';')[0]) or len(
			glob.glob(self.ui.filePath.text().split(';')[0])) >= 1

		if not state:
			self.sender().setStyleSheet('background-color: red; color: black;')

		else:
			self.sender().setStyleSheet('background-color: black; color: orange;')

		self.ui.addToTable.setEnabled(state)

	def addData(self):
		'''Завантаження даних з файлів'''

		paths = self.ui.filePath.text()
		print(paths)
		for path in paths.split(';'):
			mselect = glob.glob(path)
			if len(mselect) >= 1:
				print(mselect)
			for path in mselect:
				if os.path.exists(path):
					# try:
					MAIN_DIRECTORY = os.path.dirname(path)
					self.PATH = MAIN_DIRECTORY
					attr = self.getUi([i + 'Column' for i in ('x', 'y', 'm')])
					xc = attr[0].value()
					yc = attr[1].value()
					mc = attr[2].value()
					try:
						x, y, m = [], [], []
						if path.split('.')[-1] == 'npy':
							data = sp.load(path)
						elif isIndicatrixData(path):
							data = indicatrixRaw2Data(path,self.filtCalc)
							xc = 0
							yc = 1
						else:
							try:
								data = sp.loadtxt(path, delimiter=self.getDelimiter())
							except:
								try:
									data = sp.loadtxt(path)
									
								except:
									# Якщо якийсь йолоп зберігає числа з комами, то ця плюшка спробує якось завантажити дані
									traceback.print_exc()
									with open(path) as f:
										for i in range(50):
											line = f.readline()
											if line[0]=='#':
												pass
											else:
												break
									nCols = len(line.split(self.getDelimiter()))
									print('nCols=',nCols)
									conv = lambda valstr: float(valstr.decode("utf-8").replace(',', '.'))
									c = {i: conv for i in range(nCols)}
									data = sp.genfromtxt(path, delimiter=self.getDelimiter(), dtype=float, converters=c)
						#print(data)
						x, y = data[:, [xc, yc]].T
					except:
						traceback.print_exc()
					print(self.ui.isNormColumn.isChecked())
					if self.ui.isNormColumn.isChecked():
						m = data[:, mc]
						col = self.ui.Norm_col_select.currentText()
						mPow = self.ui.Norm_Col_Pow.value()
						kk =	 1.2/1.9
						m = (medfilt(m*kk,7))**mPow
						#m = (m)**mPow

						if col == "All":
							XY = sp.array([x / m, y / m]).T
						elif col == "X":
							XY = sp.array([x / m, y]).T
						elif col == "Y":
							XY = sp.array([x, y / m]).T
					else:
						XY = sp.array([x, y]).T
					# XY = XY[XY[:,0] != 0]
					# XY = XY[XY[:,1] != 0]

					# усереднення з кроком по N імпульсів
					if self.ui.startStepAverage.isChecked():
						XY = sp.vstack(
							[i.mean(axis=0) for i in sp.array_split(XY, len(XY) // self.ui.startStepAverage_N.value())])

					# Виділення напрямку переміщення клину
					p = -1
					pathIndex = self.ui.selectPartOfData.currentIndex()
					if pathIndex == 1:
						p = sp.where(XY[:, 0] == XY[:, 0].max())[0][0]
						XY = XY[:p, :]
					elif pathIndex == 2:
						p = sp.where(XY[:, 0] == XY[:, 0].max())[0][0]
						XY = XY[p:, :]
					else:
						pass

					if self.ui.autoSortData.isChecked():
						XY = XY[sp.argsort(XY[:, 0])]

					Name = os.path.splitext(os.path.basename(path))[0]

					color = 'cyan'
					state = 1  # ---------------------------------------------
					
					if state:
						self.addNewData(data=XY, scales=[0, 0], name=Name, color=color, xc=xc, yc=yc)

						# ’’зсув в 0’’

						if self.getUi('shift0').isChecked():
							self.norm_Shift0()

						# except (ValueError, IOError, IndexError):
						#	self.mprintf("loadData: readError")
				else:
					print('loadData: pathError', type="error")

	def updateNamesTable(self):
		c = self.ui.namesTable.rowCount()
		self.nameBox.clear()
		c1 = self.ui.normTable.rowCount()
		for i in range(c):
			self.nameBox.addItem(self.ui.namesTable.item(i, 0).text())
		for j in range(c1):
			lastCell0 = self.ui.normTable.cellWidget(j, 0).currentText()
			self.ui.normTable.cellWidget(j, 0).clear()
			#lastCell1 = self.ui.normTable.cellWidget(j, 1).currentText()
			#self.ui.normTable.cellWidget(j, 1).clear()
			#lastInd = [0, 0]
			for i in range(c):
				text = self.ui.namesTable.item(i, 0).text()
				print(text, lastCell0)
				#if text == lastCell0:
				#	lastInd[0] = i
				#elif text == lastCell1:
				#	lastInd[1] = i
				self.ui.normTable.cellWidget(j, 0).addItem(text)
				#self.ui.normTable.cellWidget(j, 1).addItem(text)
				#self.ui.normTable.cellWidget(j, 1)
			#self.ui.normTable.cellWidget(j, 0).setCurrentIndex(lastInd[0])
			#self.ui.normTable.cellWidget(j, 1).setCurrentIndex(lastInd[1])
		if hasattr(self, 'intensDialog'):
			self.intensDialog.updateActiveDataList()

	def editTableItemName(self, item):

		if item.column() == 0 and self.confDict['tableEditedName'] and not self.confDict['nameEditLock'] \
				and item.text() not in self.data.keys():

			print(self.confDict['tableEditedName'], item.text(), self.data.keys())
			self.data[item.text()] = self.data[self.confDict['tableEditedName']]
			del self.data[self.confDict['tableEditedName']]
			self.ui.namesTable.item(item.row(), 0).setText(item.text())
			print(self.confDict['tableEditedName'], "\t-->\t", item.text(), "\t|\t", self.data.keys())
			self.confDict['nameEditLock'] = True
			print(dir(item))
			self.updateNamesTable()
		# self.ui.namesTable.resizeColumnsToContents()


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
			col = QtWidgets.QColorDialog.getColor()
			self.ui.namesTable.item(clicked.row(), 2).setBackground(col)

			self.updateData(item0.text(), color=col.name())

	def currentName(self):
		'''Назва активних даних'''
		row = self.ui.namesTable.currentRow()
		if self.ui.namesTable.item(row, 0) is None:
			print('Name: None')
			return None
		else:
			return self.ui.namesTable.item(row, 0).text()

	def tableItemChanged(self, item):
		if not item is None:
			Name = item.text()
			if Name in self.data.keys():
				state = False
				if len(self.data[Name]['main']) > 1:
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
			if row < self.ui.namesTable.rowCount() - 1:
				self.ui.namesTable.insertRow(row + 2)
				for i in range(self.ui.namesTable.columnCount()):
					self.ui.namesTable.setItem(row + 2, i, self.ui.namesTable.takeItem(row, i))
					self.ui.namesTable.setCurrentCell(row + 2, 0)
				self.ui.namesTable.removeRow(row)

		if action == "Up":
			row = self.ui.namesTable.currentRow()
			column = self.ui.namesTable.currentColumn();
			if row > 0:
				self.ui.namesTable.insertRow(row - 1)
				for i in range(self.ui.namesTable.columnCount()):
					self.ui.namesTable.setItem(row - 1, i, self.ui.namesTable.takeItem(row + 1, i))
					self.ui.namesTable.setCurrentCell(row - 1, 0)
				self.ui.namesTable.removeRow(row + 1)
		self.updateNamesTable()

	def deleteFromTable(self):
		# try:

		selected = self.ui.namesTable.selectionModel().selectedIndexes()
		rows = []
		names = []
		for i in selected:
			rows.append(i.row())
			name = self.ui.namesTable.item(i.row(), 0).text()
			# del self.data[name]['main']
			print(self.data.keys(), name)
			names.append(name)
		print(rows)
		rows.sort()
		for i in rows[::-1]:
			print(i)
			self.ui.namesTable.removeRow(i)
			self.nameBox.removeItem(i)

		print("-" * 10)
		for i in names:
			print('deleted:', self.data.keys(), i)
			del self.data[i]
			if i in self.selectedDataDict.keys():
				self.selectedDataDict.pop(i, None)
		print(self.data.keys())
		self.updateNamesTable()

	def multiPlot(self):
		selected = self.ui.namesTable.selectionModel().selectedIndexes()
		lines = []
		for i in selected:
			name = self.ui.namesTable.item(i.row(), 0).text()
			data, _ = self.getData(name)
			modifiers = QtWidgets.QApplication.keyboardModifiers()
			if modifiers == QtCore.Qt.ControlModifier:
				lines.append(self.mpl.canvas.ax.plot(data[:, 0], data[:, 1], ".", color=data.attrs['color'], alpha=0.5)[0])
			else:

				lines.append(self.mpl.canvas.ax.plot(data[:, 0], data[:, 1], ".", color=data.attrs['color'])[0])
				lines.append(self.mpl.canvas.ax.plot(data[:, 0], data[:, 1], "-", color=data.attrs['color'], alpha=0.6)[0])
		self.mpl.canvas.draw()
		for i in lines:
			self.mpl.canvas.ax.lines.remove(i)

	def joinDataArrays(self):
		""" Зшивання даних"""
		selected = self.ui.namesTable.selectionModel().selectedIndexes()
		dList = []
		nList = []
		for i in selected:
			name = self.ui.namesTable.item(i.row(), 0).text()
			data, _ = self.getData(name)
			dList.append(data[:,:2])
			nList.append(name)
		Data = sp.vstack(dList)
		Name = "+".join(nList)
		self.addNewData(name=Name, data=Data)

	###########################################################################
	######################	Нормування даних	###############################
	###########################################################################
	def flipData(self):
		""" Розвернути дані """
		data, Name = self.getData()
		data[:, 0] = -data[:, 0][::-1]

		data[:, 1] = data[:, 1][::-1]
		self.updateData(name=Name, data=data)

	def movePoint(self):
		'''Переміщення точок'''
		data, Name = self.getData()
		if not data is None:
			def on_motion(event):
				if not event.xdata is None and not event.ydata is None:
					xl = self.mpl.canvas.ax.get_xlim()
					yl = self.mpl.canvas.ax.get_ylim()
					self.mpl.canvas.ax.figure.canvas.restore_region(self.background)
					self.mpl.canvas.ax.set_xlim(xl)
					self.mpl.canvas.ax.set_ylim(yl)
					nearest_x = sp.absolute(data[:, 0] - event.xdata).argmin()
					# print(nearest_x, data[nearest_x, 1], event.xdata)
					yl = self.mpl.canvas.ax.get_ylim()
					self.line.set_xdata([event.xdata] * 2)
					self.line.set_ydata(yl)
					self.points.set_xdata(data[nearest_x, 0])
					self.points.set_ydata(data[nearest_x, 1])
					# redraw artist
					self.mpl.canvas.ax.draw_artist(self.line)
					self.mpl.canvas.ax.draw_artist(self.points)
					self.mpl.canvas.ax.figure.canvas.blit(self.mpl.canvas.ax.bbox)

			def on_press(event):
				if not event.xdata is None and not event.ydata is None:

					nearest_x = abs(data[:, 0] - event.xdata).argmin()
					# nearest_y = abs(data[:, 1] - event.ydata).argmin()

					data[nearest_x, 1] = event.ydata
					self.updateData(name=Name, data=data)

					xl = self.mpl.canvas.ax.get_xlim()
					self.mpl.canvas.ax.plot(xl, [1] * 2, '-.r')
					self.mpl.canvas.ax.plot(event.xdata, 1, 'ro', markersize=6)
					self.mpl.canvas.draw()
					self.mpl.canvas.mpl_disconnect(self.cidpress)
					self.mpl.canvas.mpl_disconnect(self.cidmotion)
				else:
					self.mpl.canvas.mpl_disconnect(self.cidpress)
					self.mpl.canvas.mpl_disconnect(self.cidmotion)

			self.cidmotion = self.mpl.canvas.mpl_connect(
				'motion_notify_event', on_motion)
			self.cidpress = self.mpl.canvas.mpl_connect(
				'button_press_event', on_press)
	
	def find_2Tangent(self, state):
		'''Переміщення точок'''
		data, Name = self.getData()
		self.issecond = 0
		if not data is None:
			X, Y = data[:,0],data[:,1]
			t = interp.InterpolatedUnivariateSpline(X, Y)
			dt = t.derivative()
			def find_tangent_line_l(x,y):
				w = X<=x
				XX = X[w]
				YY = Y[w]
				r = abs(YY-y+dt(XX)*(x-XX))
				w = sp.where(r == r.min())[0]
				f = lambda x: YY[w]+dt(XX[w])*(x-XX[w])
				return f
			def find_tangent_line_r(x,y):
				w = X>=x
				XX = X[w]
				YY = Y[w]
				r = abs(YY-y+dt(XX)*(x-XX))
				w = sp.where(r == r.min())[0]
				f = lambda x: YY[w]+dt(XX[w])*(x-XX[w])
				return f
			k = 0
			def on_motion(event):
				if not event.xdata is None and not event.ydata is None:
					xl = self.mpl.canvas.ax.get_xlim()
					yl = self.mpl.canvas.ax.get_ylim()
					self.mpl.canvas.ax.figure.canvas.restore_region(self.background)
					self.mpl.canvas.ax.set_xlim(xl)
					self.mpl.canvas.ax.set_ylim(yl)
					# print(nearest_x, data[nearest_x, 1], event.xdata)
					yl = self.mpl.canvas.ax.get_ylim()
					
					yy_l = find_tangent_line_l(event.xdata, event.ydata)
					yy_r = find_tangent_line_r(event.xdata, event.ydata)
					x_new = sp.array([xl[0],event.xdata,xl[1]])
					y_new = sp.array([yy_l(xl[0]), yy_l(event.xdata), yy_r(xl[1])])
					self.line.set_data(x_new, y_new)
					#self.points.set_xdata(data[nearest_x, 0])
					#self.points.set_ydata(data[nearest_x, 1])
					# redraw artist
					self.mpl.canvas.ax.draw_artist(self.line)
					#self.mpl.canvas.ax.draw_artist(self.points)
					self.mpl.canvas.ax.figure.canvas.blit(self.mpl.canvas.ax.bbox)

			def on_press(event):

				if not event.xdata is None and not event.ydata is None:
					
					self.mpl.canvas.ax.plot(event.xdata, event.ydata,'ro', markersize=6)
					self.mpl.canvas.draw()
					self.mpl.canvas.mpl_disconnect(self.cidpress)
					self.mpl.canvas.mpl_disconnect(self.cidmotion)
					print('press')
					self.ui.action_find2Tangent.setChecked(False)
					self.mprintf("XY: %.3f, %.3f"%(event.xdata, event.ydata))

				else:
					self.mpl.canvas.mpl_disconnect(self.cidpress)
					self.mpl.canvas.mpl_disconnect(self.cidmotion)
				
		if state:
			self.cidpress = self.mpl.canvas.mpl_connect(
				'button_press_event', on_press)
			self.cidmotion = self.mpl.canvas.mpl_connect(
				'motion_notify_event', on_motion)


		else:
			try:
				self.mpl.canvas.mpl_disconnect(self.cidpress)
				self.mpl.canvas.mpl_disconnect(self.cidmotion)
				#self.update_graph()
				self.ui.action_find2Tangent.setChecked(False)

			except:
				traceback.print_exc()

	def norm_FirstPoint(self):
		''' Нормування на першу точку '''

		data, Name = self.getData()
		if not data is None:
			try:
				data[:, 1] /= self.abs(data[0, 1])
				self.updateData(name=Name, data=data)
				xl = self.mpl.canvas.ax.get_xlim()
				l1, = self.mpl.canvas.ax.plot(xl, [1] * 2, 'r')
				l2, = self.mpl.canvas.ax.plot(data[0, 0], 1, 'ro', markersize=6)
				self.mpl.canvas.draw()
				self.mpl.canvas.ax.lines.remove(l1)
				self.mpl.canvas.ax.lines.remove(l2)

			except:
				traceback.print_exc()
			# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)

	def norm_Max(self):
		''' Нормування на максимум '''
		data, Name = self.getData()
		if not data is None:
			try:
				data[:, 1] /= self.abs(data[:, 1].max())
				self.updateData(name=Name, data=data)
			except:
				traceback.print_exc()
		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)

	'''
	def decor(f):
		@wraps(f)
		def func_wrapper(Self):
			Name = Self.currentName()
			Self.processSelectedData(Name, Self.sender)
			print("sdf")
			return f(Self)
		return func_wrapper

	@decor
	'''

	def norm_Shift0X(self):
		''' Центрування по X'''

		data, Name = self.getData()

		if not data is None:
			try:
				data[:, 0] = data[:, 0] - (data[:, 0] * data[:, 1]).sum() / data[:,
																			1].sum()  # data[data[:,1]>=data[:,1].max()*0.8, 0].mean()

				self.updateData(name=Name, data=data)
			except:
				traceback.print_exc()
		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)

	def norm_AtX(self):
		''' Нормувати на 1 по заданому X'''
		self.ui.stackedWidget.setCurrentWidget(self.getUi('page_NormShift'))
		data, Name = self.getData()

		if not data is None:
			try:
				p = self.ui.norm_at_X.value()
				y1 = interp.interp1d(data[:,0], data[:,1])(p)
				data[:,1] /= self.abs(y1)
				self.updateData(name=Name, data=data)
			except:
				traceback.print_exc()
		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)

	def norm_Shift0Xh(self, state):
		''' Центрування по X вручну'''

		data, Name = self.getData()


		def on_press(event):
			''' Отримання координат точки для нормування на точку '''
			if not event.xdata is None and not event.ydata is None:

				if not data is None:
					data[:, 0] -= event.xdata  # data[data[:,1]>=data[:,1].max()*0.8, 0].mean()

					self.updateData(Name, data=data)
					yl = self.mpl.canvas.ax.get_ylim()
					self.line, = self.mpl.canvas.ax.plot([0] * 3, [yl[0], (yl[0]+yl[1])/2, yl[1]], 'r')
					# self.points, = self.mpl.canvas.ax.plot(0, yl, 'ro', markersize=6)
					self.mpl.canvas.draw()
					self.mpl.canvas.mpl_disconnect(self.cidpress)
					self.mpl.canvas.mpl_disconnect(self.cidmotion)
					self.ui.norm_Shift0Xh.setChecked(False)

		def on_motion(event):
			if not event.xdata is None and not event.ydata is None:
				xl = self.mpl.canvas.ax.get_xlim()
				yl = self.mpl.canvas.ax.get_ylim()
				self.mpl.canvas.ax.figure.canvas.restore_region(self.background)
				self.mpl.canvas.ax.set_xlim(xl)
				self.mpl.canvas.ax.set_ylim(yl)

				self.line.set_xdata([event.xdata] * 2)
				self.line.set_ydata(yl)

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
		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)

	def norm_ShiftRange(self, state):
		'''Переміщення точок'''
		Data, Name = self.getData()
		data = Data[:]
		if not data is None:

			def on_release1(event):
				if not event.xdata is None and not event.ydata is None:
					xy = self.mplSpan.get_xy()
					xmin = xy[:, 0].min()
					xmax = xy[:, 0].max()
					w = (data[:, 0] > xmin) * (data[:, 0] < xmax)
					tmp = data[:]
					self.points, = self.mpl.canvas.ax.plot(tmp[w][:, 0].mean(), tmp[w][:, 1].mean(), '+r',
														   markersize=16, zorder=20, alpha=1)

					self.mpl.canvas.draw()

					p = self.points  # [0]
					if p.get_alpha():
						p.set_alpha(p.get_alpha() * 0.5)
					else:
						p.set_alpha(0.8)
					self.mpl.canvas.mpl_disconnect(self.cidmotion)

			def on_motion1(event):
				if not event.xdata is None and not event.ydata is None and self.issecond:
					# self.mpl.canvas.ax.figure.canvas.restore_region(self.background)
					xy = self.mplSpan.get_xy()
					self.mplSpan.set_xy([xy[0], xy[1], [event.xdata, xy[1][1]], [event.xdata, xy[0][1]]])

					# redraw artist
					self.mpl.canvas.ax.draw_artist(self.mplSpan)

					self.mpl.canvas.ax.figure.canvas.blit(self.mpl.canvas.ax.bbox)

			def on_first_press1(event):
				if not self.issecond:
					if not event.xdata is None and not event.ydata is None:
						if not hasattr(self, 'mplSpan'):
							self.mplSpan = self.mpl.canvas.ax.axvspan(event.xdata, event.xdata, facecolor='g',
																	  alpha=0.5)
						else:
							yl = self.mpl.canvas.ax.get_ylim()
							self.mplSpan.set_xy([[event.xdata, yl[0]], [event.xdata, yl[1]], [event.xdata, yl[1]],
												 [event.xdata, yl[0]]])
						self.mpl.canvas.draw()
					# self.mpl.canvas.mpl_disconnect(self.cidpress)
					# self.mpl.canvas.mpl_disconnect(self.cidmotion)
					else:
						self.mpl.canvas.mpl_disconnect(self.cidpress)
						self.mpl.canvas.mpl_disconnect(self.cidmotion)
					self.issecond = True
				else:
					if not event.xdata is None and not event.ydata is None:
						self.issecond = False
						xy = self.mplSpan.get_xy()
						xmin = xy[:, 0].min()
						xmax = xy[:, 0].max()
						w = (data[:, 0] > xmin) * (data[:, 0] < xmax)
						print(xmin, xmax, w.sum())

						m = data[:, 1][w].mean()
						modifiers = QtWidgets.QApplication.keyboardModifiers()
						if modifiers == QtCore.Qt.ControlModifier:
							data[:,1][w] = sp.log10(10**data[:,1][w]*10**(self.abs(event.ydata)) / 10**self.abs(m))
						else:
							data[:, 1][w] *= self.abs(event.ydata) / self.abs(m)
						Data[:] = data
						self.updateData(name=Name, data=Data)
						self.mpl.canvas.mpl_disconnect(self.cidpress)
						self.mpl.canvas.mpl_disconnect(self.cidmotion)
						self.ui.norm_ShiftRange.setChecked(False)
					else:
						self.mpl.canvas.mpl_disconnect(self.cidpress)
						self.mpl.canvas.mpl_disconnect(self.cidmotion)

		if state:
			self.cidmotion = self.mpl.canvas.mpl_connect(
				'motion_notify_event', on_motion1)
			self.cidpress = self.mpl.canvas.mpl_connect(
				'button_press_event', on_first_press1)
			self.cidrelease = self.mpl.canvas.mpl_connect(
				'button_release_event', on_release1)

		else:
			try:
				if hasattr(self, 'cidpress'):
					self.mpl.canvas.mpl_disconnect(self.cidpress)
				if hasattr(self, 'cidmotion'):
					self.mpl.canvas.mpl_disconnect(self.cidmotion)
				if hasattr(self, 'cidrelease'):
					self.mpl.canvas.mpl_disconnect(self.cidrelease)

				self.update_graph()
			except:
				traceback.print_exc()
	def ShiftXY(self):
		data, Name = self.getData()
		shiftX = self.ui.ShiftXVal.value()
		shiftY = self.ui.ShiftYVal.value()

		data[:,0] -= shiftX
		data[:,1] -= shiftY
		self.updateData(name=Name, data=data)
		
		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)
		
	def norm_Shift0(self):
		''' Видалення фонової компоненти '''
		# Name = self.currentName()
		self.ui.stackedWidget.setCurrentWidget(self.getUi('page_NormShift'))
		shift_len = self.ui.norm_Shift0_len.value()
		data, Name = self.getData()
		newData = sp.copy(data)
		if not data is None:
			try:
				p = int(len(data) / shift_len)
				eq = sp.poly1d(sp.polyfit(data[:p, 0], data[:p, 1], 1))
				y0 = eq(0.)
				print(y0)
				l1, = self.mpl.canvas.ax.plot(data[:p, 0], eq(data[:p, 0]), 'r-', markersize=6)
				self.mpl.canvas.draw()
				self.mpl.canvas.ax.lines.remove(l1)
				newData[:, 1] -= y0

				# data[:, 1] /= data[:, 1].max()
				self.updateData(name=Name, clone=data, data=(newData))
				l1, = self.mpl.canvas.ax.plot(data[:p, 0], eq(data[:p, 0]), 'r-', markersize=6)
				self.mpl.canvas.draw()
				self.mpl.canvas.ax.lines.remove(l1)


				# Якщо ввімкнено, обробка решти даних
				self.processSelectedData(Name, self.sender)
			except:
				traceback.print_exc()

	def norm_Point(self, state):
		''' Нормувати на вказану точку '''
		data, Name = self.getData()

		def on_press(event):
			''' Отримання координат точки для нормування на точку '''
			if not event.xdata is None and not event.ydata is None:

				if not data is None:
					data[:, 1] /= self.abs(event.ydata)
					self.updateData(Name, data=data)
					xl = self.mpl.canvas.ax.get_xlim()
					self.mpl.canvas.ax.plot(xl, [1] * 2, 'r')
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
				self.line.set_ydata([event.ydata] * 2)

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
		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)

	###########################################################################
	######################	Масштаби 	###############################
	###########################################################################
	# Повернути масштаб при поверненні в історії
	def setPrevScale(self):
		actions = ('actionY_X', 'actionX_Log10', 'actionY_Log10')

		data, Name = self.getData()
		if not data is None:
			scale = data.attrs['scales']
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
			ui_actions[0].setEnabled(not (ui_actions[1].isChecked() or ui_actions[2].isChecked()))
			ui_actions[1].setEnabled(not ui_actions[0].isChecked())
			ui_actions[2].setEnabled(not ui_actions[0].isChecked())

			for t in ui_actions:
				t.toggled[bool].connect(self.setNewScale)

	# Змінити масштаб на новий
	def setNewScale(self, state):
		actions = ('actionY_X', 'actionX_Log10', 'actionY_Log10')
		senderName = self.sender().objectName()
		data, Name = self.getData()
		comment = {}
		shiftForLog10 = None
		if not data is None:
			Scale = data.attrs['scales']
			# print("Scales:\t", Scale)
			# ui_obj = self.getUi([t + i for i in Names])
			ui_actions = self.getUi(actions)
			if senderName == actions[0]:
				# ui_obj = getattr(self.ui, t + "LogScale")
				if state:
					Scale[1] = 2
					# bb = data[:, 0]!=0
					# print(bb)
					data = data[data[:, 0] != 0, :]
					data[:, 1] = data[:, 1] / data[:, 0]
				else:
					Scale[1] = 0
					data[:, 1] = data[:, 1] * data[:, 0]
				for i in ui_actions[1:]:
					i.setEnabled(not ui_actions[0].isChecked())

			else:
				index = int(senderName[6] != "X")
				# ui_obj = getattr(self.ui, t + Names[0])
				# print(Scale, state)

				if state == 1:
					logShift = data[:, index].min()
					print("logShift=%f" % logShift)
					if logShift < 0 and self.ui.Log10Shift.isChecked():
						shiftForLog10 = logShift
						data[:, index] -= logShift

					data = data[data[:, index] > 0, :]
					data[:, index] = sp.log10(data[:, index])
				else:

					data[:, index] = sp.power(10., data[:, index])
					if data.attrs['shiftForLog10'] != None and self.ui.Log10Shift.isChecked():
						data[:, index] += data.attrs['shiftForLog10']
						shiftForLog10 = None
				Scale[index] = int(state)
				# print(Scale)
				# ui_obj[0].setEnabled(##	not (ui_obj[1].isChecked() or ui_obj[2].isChecked()))
				ui_actions[0].setEnabled(
					not (ui_actions[1].isChecked() or ui_actions[2].isChecked()))
			# print('Scales0: ', Scale)
			self.updateData(name=Name, data=data, scales=Scale, shiftForLog10=shiftForLog10, showTmp=False)

			# Якщо ввімкнено, обробка решти даних
			self.processSelectedData(Name, self.sender)

	###########################################################################
	######################	Графічні методи 	###############################
	###########################################################################
	def Rescale(self,data=None):

		try:
			XY = None
			if data is None:
				XY, _ = self.getData()
			else:
				XY = data
			xMargin = abs(XY[:, 0].max() - XY[:, 0].min()) * 0.05
			yMargin = abs(XY[:, 1].max() - XY[:, 1].min()) * 0.05
			print(xMargin, ":", yMargin)
			if sp.isnan(xMargin):
				print(xMargin)
				xMargin = 0
			if sp.isnan(yMargin):
				print(yMargin)
				yMargin = 0

			self.mpl.canvas.ax.set_xlim((XY[:, 0].min() - xMargin, \
										 XY[:, 0].max() + xMargin))
			self.mpl.canvas.ax.set_ylim((XY[:, 1].min() - yMargin, \
										 XY[:, 1].max() + yMargin))
			yl = self.mpl.canvas.ax.get_ylim()
			self.mplSpan.set_xy([[0, yl[0]], [0, yl[1]], [0, yl[1]], [0, yl[0]]])
		except:
			traceback.print_exc()

	def update_graph(self, name=None, data=None, showTmp=True):
		"""Updates the graph with new X and Y"""
		# TODO: rewrite this routine, to get better performance


		self.background = \
			self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
		# save current plot variables
		if name is None:
			data, name = self.getData()

		if data is None:
			data, _ = self.getData(name)
		if name is None:
			print('noData')
		else:
			print("points: %d"% len(data))
			if self.confDict['autoscale'] and len(data) > 2:
				self.Rescale(data)

			if self.background != None:
				# save initial x and y limits
				self.xl = self.mpl.canvas.ax.get_xlim()
				self.yl = self.mpl.canvas.ax.get_ylim()

			# clear the axes
			self.mpl.canvas.ax.clear()
			# plot graph
			self.mpl.canvas.ax.axis[:].invert_ticklabel_direction()
			# self.mpl.canvas.ax.set_xticks(self.mpl.canvas.ax.get_xticks()[1:-1])


			if self.confDict['showTmp'] and len(self.data[name]['main']) > 1 and showTmp:
				# print(data.attrs['color'])
				prev_data = self.data[name]['main'][str(int(self.dIndex(name)) - 1)]
				c = QtGui.QColor(data.attrs['color']).getRgb()
				new_color = QtGui.QColor(255 - c[0], 255 - c[1], 255 - c[2], 255)
				self.plt_tmp, = self.mpl.canvas.ax.plot(prev_data[:, 0], \
														prev_data[:, 1], color=new_color.name(), marker='+',
														linestyle='None', markersize=4, alpha=0.35)

			self.plt, = self.mpl.canvas.ax.plot(data[:, 0], \
												data[:, 1], color=data.attrs['color'], marker='o', linestyle='None',
												markeredgecolor=data.attrs['color'], markersize=5, zorder=15, alpha=0.9)
			self.plt, = self.mpl.canvas.ax.plot(data[:, 0], \
												data[:, 1], color=data.attrs['color'],  linestyle='-',
												markeredgecolor=data.attrs['color'],  zorder=16, alpha=0.3)
			self.mprintf(len(data))
			if not hasattr(self, 'line'):
				# creating line
				self.line, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'g--', animated=True)
			if not hasattr(self, 'points'):
				# creating points
				self.points, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'mo', animated=True, markersize=3)
			if not hasattr(self.ui, 'rectab'):
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


			# self.set_x_log(self.ui.xLogScale.isChecked(), redraw = False)
			# self.set_y_log(self.ui.yLogScale.isChecked(), redraw = False)
			# force an image redraw
			self.mpl.canvas.draw()

			# copy background
			self.background = \
				self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
			# make edit buttons enabled

			self.ui.mplactionCut_by_line.setEnabled(self.background != None)
			self.ui.mplactionCut_by_rect.setEnabled(self.background != None)

		# self.mpl.canvas.ax.relim()
		# self.mpl.canvas.ax.autoscale_view()

		# if sp.shape(data) != self.tempShape :
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

	def cut_line(self, state):
		"""start cut the line"""
		if state:

			# self.sdata = data.copy()
			self.cidpress = self.mpl.canvas.mpl_connect(
				'button_press_event', self.on_press)
			self.cidrelease = self.mpl.canvas.mpl_connect(
				'button_release_event', self.on_release)
		else:
			self.issecond = 0
			self.mpl.canvas.mpl_disconnect(self.cidpress)
			self.mpl.canvas.mpl_disconnect(self.cidrelease)
			if hasattr(self, 'cidmotion'):
				self.mpl.canvas.mpl_disconnect(self.cidmotion)
			self.update_graph()
		self.ui.mplactionCut_by_rect.setEnabled(not state)
		self.ui.stackedWidget.setEnabled(not state)

	def on_press(self, event):
		"""on button press event for line
		"""
		if not event.xdata is None and not event.ydata is None:
			# copy background

			self.background = \
				self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
			if self.issecond == 0:
				self.x1 = event.xdata
				self.y1 = event.ydata
				self.cidmotion = self.mpl.canvas.mpl_connect('motion_notify_event', self.on_motion)
				return

			if self.issecond == 1:
				data, name = self.getData()

				self.x3 = event.xdata
				self.y3 = event.ydata
				# point swap
				if self.x1 >= self.x2:
					self.x1, self.x2 = swap(self.x1, self.x2)
					self.y1, self.y2 = swap(self.y1, self.y2)
				try:
					y = ((self.y2 - self.y1) / (self.x2 - self.x1)) * \
						(self.x3 - self.x2) + self.y2
					X = data[:, 0]
					Y = data[:, 1]
					yy = ((self.y2 - self.y1) / (self.x2 - self.x1)) * \
						 (X - self.x2) + self.y2
				except:
					y = 0.
				if self.y3 >= y:
					# up cut
					w = (X >= self.x1) * (X <= self.x2) * (Y >= yy)
					data = data[~w, :]

				else:
					# down cut
					w = (X >= self.x1) * (X <= self.x2) * (Y <= yy)
					data = data[~w, :]
				self.updateData(name, data=data)

				self.ui.mplactionCut_by_line.setChecked(False)
		else:

			#self.ui.mplactionCut_by_line.setChecked(False)
			return

	def on_motion(self, event):
		'''on motion we will move the rect if the mouse is over us'''
		if not event.xdata is None and not event.ydata is None:
			self.x2 = event.xdata
			self.y2 = event.ydata
			self.draw_line()
		else:
			pass
			#self.ui.mplactionCut_by_line.setChecked(False)

	def on_release(self, event):
		'''on release we reset the press data'''
		if not event.xdata is None and not event.ydata is None:
			self.x2 = event.xdata
			self.y2 = event.ydata
			self.issecond = 1
			self.draw_line()
			if self.x1 and self.x2 and self.y1 and self.y2:
				# self.mpl.canvas.mpl_disconnect(self.cidpress)
				self.mpl.canvas.mpl_disconnect(self.cidmotion)
				self.mpl.canvas.mpl_disconnect(self.cidrelease)
			else:
				self.mpl.canvas.mpl_disconnect(self.cidpress)
		else:
			self.x2 = self.line.get_xdata()[-1]
			self.y2 = self.line.get_ydata()[-1]
			self.issecond = 1
			#self.draw_line()
			if self.x1 and self.x2 and self.y1 and self.y2:
				# self.mpl.canvas.mpl_disconnect(self.cidpress)
				self.mpl.canvas.mpl_disconnect(self.cidmotion)
				self.mpl.canvas.mpl_disconnect(self.cidrelease)
			else:
				self.mpl.canvas.mpl_disconnect(self.cidpress)
			#self.ui.mplactionCut_by_line.setChecked(False)

	############################### Rect ####################################
	def cut_rect(self, state):
		if state:
			"""start to cut the rect"""
			# self.sdata = data.copy()
			self.cidpress = self.mpl.canvas.mpl_connect(
				'button_press_event', self.on_press2)
			self.cidrelease = self.mpl.canvas.mpl_connect(
				'button_release_event', self.on_release2)
		else:
			self.issecond = 0
			self.mpl.canvas.mpl_disconnect(self.cidpress)
			self.mpl.canvas.mpl_disconnect(self.cidrelease)
			if hasattr(self, 'cidmotion'):
				self.mpl.canvas.mpl_disconnect(self.cidmotion)
			self.update_graph()
		self.ui.mplactionCut_by_line.setEnabled(not state)
		self.ui.stackedWidget.setEnabled(not state)

	def on_press2(self, event):
		"""on button press event for rectangle
		"""
		if not event.xdata is None and not event.ydata is None:
			# copy background

			self.background = \
				self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
			# first press
			if self.issecond == 0:
				self.x1 = event.xdata
				self.y1 = event.ydata

				self.cidmotion = self.mpl.canvas.mpl_connect('motion_notify_event', self.on_motion2)
				return
			# second press
			if self.issecond == 1:
				data, name = self.getData()
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
				X = data[:, 0]
				Y = data[:, 1]
				w = (X >= self.x1) * (X <= self.x2) * (Y <= self.y1) * (Y >= self.y2)
				if self.y3 <= self.y1 and self.y3 >= self.y2 and self.x3 >= self.x1 and self.x3 <= self.x2:
					# in cut
					data = data[~w, :]
				else:
					# out cut
					data = data[w, :]

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
				# self.mpl.canvas.mpl_disconnect(self.cidpress)
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
		# self.Rescale()
		else:
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
			X = data[:, 0]
			Y = data[:, 1]
			if self.ui.FiltFiltY.isChecked():
				Y = filtfilt(b, a, Y)
			if self.ui.FiltFiltX.isChecked():
				X = filtfilt(b, a, X)

			self.updateData(name=Name, clone=data, data=(sp.array([X, Y]).T))

		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)

	#  page_PolyFit
	def polyApprox(self):
		''' Апроксимація поліномом n-го степ. '''
		data, Name = self.getData()
		X, Y = data[:, 0], data[:, 1]
		step = self.getUi('ApproxStep').value()
		M = self.getUi('ApproxM').value()

		EQ = sp.poly1d(sp.polyfit(X, Y, M))
		xnew = sp.arange(X.min(), X.max(), step)
		ynew = EQ(xnew)

		self.updateData(name=Name, clone=data, data=(sp.array([xnew, ynew]).T))

		if self.confDict['showTmp']:
			# self.mpl.canvas.ax.plot(x,  y, '.m',  alpha=0.2,  zorder=1)
			xl = self.mpl.canvas.ax.get_xlim()
			yl = self.mpl.canvas.ax.get_ylim()

			text = ''
			for j, i in enumerate(EQ):
				text += "+" * (i > 0) + str(i) + " x^{" + str(M - j) + "}"
			text = "$" + text[(EQ[0] > 0):] + "$"
			print(text)

		# self.mpl.canvas.ax.text(xl[0], yl[0], text, fontsize=15, color='orange')

		# self.mpl.canvas.draw()

		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)

	#  page_B_spline
	"""
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
	"""

	def B_spline(self):
		'''інтерполяція b-сплайном'''
		spins = ['B_spline' + i for i in ('Step', "K", "NKnots", "_xb", "_xe")]
		step, km, nknots, xb, xe = (i.value() for i in self.getUi(spins))
		prev_data, Name = self.getData()
		XY = prev_data[:]
		XY = XY[XY[:, 0].argsort()]

		X, Y = XY.T[:2]
		# w_tmp = (X>=X.min()*xb) * (X<=X.max()*xe)
		# Y = Y[w_tmp]
		# X = X[w_tmp]
		nknots = int(nknots)
		km = int(km)

		idx_knots = (sp.arange(1, len(X) - 1, (len(X) - 2) / sp.double(nknots))).astype('int')
		knots = X[idx_knots]
		# print(len(knots), len(X[idx_knots]), knots, X[idx_knots])
		# If task=-1 find the weighted least square spline for a given set of knots, t.
		# These should be interior knots as knots on the ends will be added automatically.

		# tck = interp.splrep(X, Y, t=knots, s=sm, k=km, task=-1, xb=X.min()/xb, xe=X.max()/xe)
		weights = (X > (X.min() * xb)) * (X < (X.max() * xe))
		# print(weights,'====================', xb, xe, X.min()*xb, X.max()*xe)
		tck = None
		try:
			tck, fp, ier, msg = interp.splrep(X, Y, w=weights, t=knots, k=km, task=-1,
											  full_output=True)  # , xb=X.min()/xb, xe=X.max()/xe)
			print("fp=%.3f\tier=%.3f\tmsg=%s" % (fp, ier, msg))
		except ValueError:
			traceback.print_exc()
			print(
				"X", X, "Y", Y, "w", weights, "knots", knots, sp.isnan(X).sum(), sp.isnan(Y).sum(),
				sp.isnan(weights).sum())

		xi = sp.arange(X.min(), X.max(), step)
		fit = interp.splev(xi, tck)

		"""
		xi = sp.arange(X.min(), X.max(),step)


		if self.getUi('B_splineSMin').isChecked():
			i = 0
			j = 0
			for i in sp.exp(sp.arange(sm,0,-sm/1000)/sm*sp.exp(1))*sm/sp.exp(1):
				if sp.isnan(interp.UnivariateSpline(X,Y, s=i, k=int(km)).get_coeffs()).sum() >0:
					break
				else:
					j = i
			sm = j

			self.getUi('B_splineS').setValue(sm)

		uspline = interp.UnivariateSpline(X,Y, s=sm, k=int(km))

		data = sp.array([xi, uspline(xi)]).T
		"""
		w = ~sp.isnan(fit)
		fit = fit[w]
		xi = xi[w]
		err = []
		if self.ui.action_ShowErrors.isChecked():
			for i in range(len(xi)):
				w = (X > xi[i] - step / 2) * (X < xi[i] + step / 2)
				try:
					err.append(sp.mean(abs(Y[w] - fit[i])))
				except ValueError:
					traceback.print_exc()
					err.append(sp.NaN)
		if not len(err) == 0:
			data = sp.array([xi, fit, err]).T
		else:
			data = sp.array([xi, fit]).T
		# data = XY.clone(data)



		# Оптимізація
		'''
		if self.getUi('B_splineSMin').isChecked():
			residuals = lambda  coeffs, xy: (xy[:,1] - sp.poly1d(coeffs)(xy[:,0]))
			uCoeffs = uspline.get_coeffs()
			plsq = leastsq(residuals, uCoeffs, args=XY)

			data = sp.array([xi, sp.poly1d(plsq[0])(xi)]).T
		'''
		self.updateData(name=Name, clone=prev_data, data=data)
		err = sp.array(err)
		xi = xi[-sp.isnan(err)]
		fit = fit[-sp.isnan(err)]
		err = err[-sp.isnan(err)]

		if self.ui.action_ShowErrors.isChecked():
			for i in range(len(xi)):
				self.mpl.canvas.ax.plot([xi[i]] * 2, [fit[i] - err[i], fit[i] + err[i]], '-r')
			self.mpl.canvas.draw()
		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)

	def poly_cut(self, data=None, N=10, m=4,
				 p=0.80, AC=False, discrete=False):
		'''	Обрізка вздовж кривої апроксиміції поліномом.
		m		-	степінь полінома
		p		-	відсоток від максимального викиду
		N		-	кількість вузлів
		AC	-	обробити Все, зробити Зріз, Зшити
		'''
		data, name = self.getData()

		X, Y = data[:, 0], data[:, 1]
		w = X.argsort()
		X, Y = X[w], Y[w]
		params = self.getUi(['Poly' + i for i in 'NPM'])
		step_size, p, m = (i.value() for i in params)

		discrete = self.ui.poly_cutDiscrete.isChecked()


		# bin_centers  = sp.arange(X.min(), X.max()-0.5*step_size,step_size)+0.5*step_size
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
		x_new = X  # sp.arange(X.min(), X.max(), step_size)
		y_new = sp.poly1d(sp.polyfit(X, Y, m))(X)
		y_wma = y_new
		y_wma = abs(Y - y_wma)
		X_new, Y_new, Y_tmp = [], [], []
		if not discrete:
			w = y_wma < y_wma.max() * p
			X_new = X[w]
			Y_new = Y[w]

		else:
			bin_centers = sp.arange(X.min(), X.max() - 0.5 * step_size, step_size) + 0.5 * step_size
			bin_size = step_size
			bin_avg = sp.zeros(len(bin_centers))

			for index in range(0, len(bin_centers)):
				bin_center = bin_centers[index]
				W = (X >= (bin_center - bin_size * 0.5)) & (X <= (bin_center + bin_size * 0.5))
				x_tmp = X[W]
				y_tmp = y_wma[W]
				if W.sum() < 1:
					continue
				else:

					w = y_tmp < y_tmp.max() * p
					X_new.append(x_tmp[w])
					Y_new.append(Y[W][w])

		X_new = sp.hstack(X_new)
		Y_new = sp.hstack(Y_new)
		out = sp.array([X_new, Y_new]).T
		Y_tmp = interp.interp1d(x_new, y_new)(X_new)

		out = out[out[:, 0].argsort()]
		# out = data.clone(out)

		self.updateData(name, clone=data, data=out)
		if self.confDict['showTmp']:
			# Y_tmp = sp.hstack(Y_tmp).T
			print(sp.shape(Y_tmp), sp.shape(out))
			# Y_tmp = Y_tmp[out[:,0].argsort()]
			self.mpl.canvas.ax.plot(out[:, 0], Y_tmp, '-r')
			self.mpl.canvas.draw()



		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(name, self.sender)

	def movingAverage(self):
		'''Ковзаюче усереднення'''
		data, name = self.getData()
		step = self.getUi('AverageStep').value()
		width = self.getUi('maWidth').value()
		try:
			x, y, err = moving_average(data[:, 0], data[:, 1], step, width)
			new_data = sp.array([x, y, err]).T
			self.updateData(name, clone=data, data=new_data)
		except:
			traceback.print_exc()
		
		if self.ui.action_ShowErrors.isChecked():
			for i in range(len(x)):
				self.mpl.canvas.ax.plot([x[i]] * 2, [y[i] - err[i], y[i] + err[i]], '-r')
			self.mpl.canvas.draw()

		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(name, self.sender)

	def setFilters(self):
		'''Посадка  на фільтри'''

		active = self.getUi([i + 'Filt' for i in ['X', 'Y']])
		res_text = self.getUi(['res' + i + 'Filt' for i in ['X', 'Y']])

		filtBaseNames = list(self.filtersDict[self.ui.filtWaveLENGTH.currentText()].keys())

		M = [1., 1.]
		for i, j in enumerate(active):
			M[i] = self.filtCalc(j.text())
			print(M[i])

		if M[0] != 1. or M[1] != 1.:
			# for i in [0,1]:	self.filtList[Name][i] = M[i]
			data, name = self.getData()
			if not data is None:
				print(M)
				for i in [0, 1]:
					if not M[i] is None:
						data[:, i] = data[:, i] / M[i]  # self.filtList[index][0]
						res_text[i].setText(str(M[i]))

				# data[:,1] = data[:,1]/M[1]  #self.filtList[index][1]
				self.updateData(name, data=data)
			# self.mprintf("Filters [X,Y]: %s" % str(self.filtList[index]))

		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(name, self.sender)

	def setFiltLineEdit(self):
		self.filtLineEdit = self.sender().objectName()[0]

	def updateFiltersList(self, index):
		''' Оновлення списку фільтрів для даної довжини хвилі'''
		fDict = self.filtersDict[self.ui.filtWaveLENGTH.currentText()]
		self.ui.filtersList.clear()
		for i in fDict:
			self.ui.filtersList.addItem(i + "\t\t" + str(fDict[i]))

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
				filters = filters.replace(' ', '').replace('+', ',').replace(';', ',').replace('\n','')
				res = 1.
				try:
					res = sp.multiply.reduce([filtTable[waveLength][i.upper()] for i in filters.split(",")])
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
			newItem = QtWidgets.QTableWidgetItem()
			self.ui.normTable.setItem(counter, i, newItem)

		combo1 = QtWidgets.QComboBox()
		combo2 = QtWidgets.QComboBox()
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

	# normButton = QtWidgets.QToolButton()
	# self.ui.normTable.setCellWidget(counter, 2, normButton)
	# saveButton = QtWidgets.QToolButton()
	# self.ui.normTable.setCellWidget(counter, 4, saveButton)


	def normDataRemove(self):
		# try:

		selected = self.ui.normTable.selectionModel().selectedIndexes()
		rows = []
		for i in selected:
			rows.append(i.row())
		# name = self.ui.normTable.item(i.row(), 0).text()
		# del self.dataDict[name]
		# print(self.dataDict.keys(), name)
		rows.sort()
		for i in rows[::-1]:
			self.ui.normTable.removeRow(i)
		# self.nameBox.removeItem(i)

	def normTableItemClicked(self, item):
		if item.column() == 2:
			name1 = self.ui.normTable.cellWidget(item.row(), 0).currentText()
			name2 = self.ui.normTable.cellWidget(item.row(), 1).currentText()
			name3 = name1 + '_' + name2
			cData, _ = self.getData(name2)
			sData, _ = self.getData(name1)
			x, y = [], []
			if cData.attrs['scales'][0] == sData.attrs['scales'][0] == 0 and \
									cData.attrs['scales'][1] == sData.attrs['scales'][1] == 0:

				# if self.ui.rButton.isEnabled():
				x = sData[:, 0]
				window = (x >= cData[:, 0].min()) * (x <= cData[:, 0].max())

				x = x[window]
				y = sData[:, 1]
				y = y[window]
				cY_tmp = sp.interpolate.interp1d(cData[:, 0], cData[:, 1], self.ui.normEvalType.currentText().lower())(
					x)
				x = x[cY_tmp != 0]
				y = y[cY_tmp != 0]

				err = []
				cY_tmp = cY_tmp[cY_tmp != 0]
				modifiers = QtWidgets.QApplication.keyboardModifiers()
				if modifiers == QtCore.Qt.ShiftModifier:
					print('Diff')
					y = y - cY_tmp
					if len(cData[:, :].T) == len(sData[:, :].T) == 3:
						sErr_tmp = sData[:, 2][cY_tmp != 0]
						cErr_tmp = sp.interpolate.interp1d(cData[:, 0], cData[:, 2],
														   self.ui.normEvalType.currentText().lower())(x)
						err = sp.sqrt(sErr_tmp ** 2 + cErr_tmp ** 2)
				else:
					y = y / cY_tmp
					if len(cData[:, :].T) == len(sData[:, :].T) == 3:
						sErr_tmp = sData[:, 2][cY_tmp != 0]
						cErr_tmp = sp.interpolate.interp1d(cData[:, 0], cData[:, 2],
														   self.ui.normEvalType.currentText().lower())(x)
						err = sp.sqrt((sErr_tmp / cY_tmp) ** 2 + (cErr_tmp * y / cY_tmp ** 2) ** 2)
						rel_err = err / y
						rel_err = rel_err[-sp.isnan(rel_err)]
						print("Mean rel. err: %.4f" % (sp.mean(rel_err)))
				print(sp.shape(x), sp.shape(y))

				# Додавання результату в звичайній формі, або в дозовій
				if not self.ui.cumSumNormData.isChecked():
					if len(err) != 0:
						outName = self.addNewData(name=name3, data=sp.array([x, y, err]).T)
						if self.ui.action_ShowErrors.isChecked():
							for i in range(len(x)):
								self.mpl.canvas.ax.plot([x[i]] * 2, [y[i] - err[i], y[i] + err[i]], '-r')
							self.mpl.canvas.draw()
					else:
						outName = self.addNewData(name=name3, data=sp.array([x, y]).T)
				else:
					outName = self.addNewData(name=name3, data=sp.array([sp.cumsum(x), y]).T)

				self.ui.normTable.item(item.row(), 3).setText(outName)
				self.ui.normTable.item(item.row(), 4).setText('Ok')
			else:
				print('ResEval: interpTypeError')

	## Chi^3
	# page_ReHi3
	def recalcReHi3(self):
		'''Обрахунок Re(hi^(3))'''

		data, Name = self.getData()

		a = self.ui.reHi3_a0.value()
		#if 'a' in data.comments and self.ui.workWithSelectedData.isChecked():
		#	a = float(data.comments['a'])
		Lambda = self.ui.reHi3_lambda.value()
		n0 = self.ui.reHi3_n0.value()
		d = self.ui.reHi3_d.value()
		z = self.ui.reHi3_z.value()
		r0 = self.ui.reHi3_r0.value()
		f = self.ui.reHi3_f.value()
		L = self.ui.reHi3_l.value()
		polyM = self.ui.reHi3_polyM.value()

		eq, na1, hi3a1, hi3t, Phit = calcReChi3(data, m=polyM, a=a, Lambda=Lambda, n0=n0, d=d, z=z, L=L, f=f, r0=r0)

		#self.updateData(name=Name, data=data, comments={'a': a})
		text = "Data name: {}\nn2 = {} ; hi3_1 = {} ; hi3_2 = {} ; Phit = {}".format(Name, na1, hi3a1, hi3t, Phit)
		print(text)
		self.ui.reHi3_console.setText(text)
		l1, = self.mpl.canvas.ax.plot(data[:, 0], sp.poly1d(eq[::-1])(data[:, 0]), 'r-', markersize=6)
		self.mpl.canvas.draw()
		self.mpl.canvas.ax.lines.remove(l1)

		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)
		print("-"*20,"CW")
		calcReChi3CW(data, m=polyM, a=a,Lambda=Lambda, n0=n0, d=d, z=z, L=L, f=f, r0=r0)

	# page_ImHi3
	def recalcImHi3(self):
		'''Обрахунок Im(hi^(3))'''

		data = []
		Name = ""
		Lambda = self.ui.imHi3_lambda.value()
		n0 = self.ui.imHi3_n0.value()
		d = self.ui.imHi3_d.value()
		exp_type = self.ui.exp_type.currentText()
		tmp = []
		if self.ui.actionProcessView.isChecked():
			name = self.currentName()

			if name in self.data:
				data = self.data[name]['main'][self.dIndex(name)]
				xl = self.mpl.canvas.ax.get_xlim()
				x_start = sp.where(data[:, 0] >= xl[0])[0][0]
				x_end = sp.where(data[:, 0] <= xl[1])[0][-1]

				#subregion = self.data[name]['tmp']['activeSubregion']
				tmp = data[x_start:x_end]
				Name = name
		else:
			data, Name = self.getData()
			tmp = data[:]
				
		#print(tmp.shape)
		ImHi3, beta, Leff, T0, x_new, y_new = calcImChi3(tmp, d=d, n0=n0, Lambda=Lambda, exp_type=exp_type)
		
		text = "Data name: {}\nLeff = {:.10g}; beta[cm/MW] = {:.10g},T_0 = {:10g}, ImChi3[esu] = {:10g}".format(Name, Leff,T0, beta, ImHi3)
		print(text)
		#self.updateData(name=Name, clone=data)#, comments=text)
		self.ui.imHi3_console.setText(text)
		l1, = self.mpl.canvas.ax.plot(x_new, y_new, 'r-', markersize=6)
		self.mpl.canvas.draw()
		self.mpl.canvas.ax.lines.remove(l1)

	## Інтенсивність
	def recalcAi2(self):
		'''Перерахунок радіусу пучка'''
		z, f, Ae = self.getValue(("Z", "F", "R"))
		length = float(self.ui.intensWaveLENGTH.currentText())
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		if modifiers == QtCore.Qt.ShiftModifier:
			pass
		else:
			Ae *= 25 * 10 ** -4
		try:
			Ai2 = 2 * Ae ** 2 * ((1 - z / f) ** 2 + (z * length * 10 ** -7 / sp.pi / Ae ** 2) ** 2) / 4
			self.ui.Ai2.setText(str(sp.sqrt(Ai2)))
		except:
			traceback.print_exc()
		# self.ui.Ai2.setText(str(sp.sqrt(Ai2)))

	def calibrCoefFromFiles(self):
		files = self.fileDialog.getOpenFileNames(self, caption="Файли калібровки", directory=self.PATH, )
		if not ScriptOptions.qt4: files = files[0]
		if files:
			print(files)
			X, Y = [], []
			for i in files:
				x, y = None, None
				name = os.path.basename(i)
				name = name.split('.dat')[0]
				print(name)
				if name.upper() == 'NULL':
					y = .0

				else:
					new_name = ''
					if len(name) >= 3:
						new_name = name[:2] + '.' + name[2:]
					elif name[0] == '0':
						new_name = name[0] + '.' + name[1:]
					else:
						new_name = name[0] + '.' + name[1:]

					y = float(new_name)
				data = sp.loadtxt(i)
				#attr = self.getUi([i + 'Column' for i in ('x', 'y', 'm')])
				
				mc = self.ui.calibrCoefColumnNorm.value() #attr[2].value()
				x = None
				if self.ui.isNormColumn.isChecked():
					m = data[:, mc]
					x = sp.mean(data[:, self.ui.calibrCoefColumn.value()] / m)
				else:
					x = sp.mean(data[:, self.ui.calibrCoefColumn.value()])
				if x != None and y != None:
					print(x, y)
					X.append(x)
					Y.append(y)
			res = sp.polyfit(X, Y, 1)[0] / sp.pi
			self.ui.calibr.setText(str(res))

			plt.plot(X, Y, 'o')
			plt.show(False)

	def recalcIntensResult(self):
		'''Перерахунок на інтенсивність
		1064: 5.03*10**-5
		532: 8.7*10**-6
		=()
		'''
		data, Name = self.getData()
		filt = self.filtCalc(self.ui.intensFilt.text(), waveLength=self.ui.intensWaveLENGTH.currentText())
		try:

			result = float(eval(self.ui.calibr.text().replace("^", "**"))) / float(self.ui.Ai2.text()) ** 2 / filt
			self.ui.intensResult.setText(str(round(result, 9)))
			
			data[:, 0] *= float(self.ui.intensResult.text())
			self.updateData(name=Name, data=data)

		except:
			traceback.print_exc()

		# Якщо ввімкнено, обробка решти даних
		self.processSelectedData(Name, self.sender)

	# =============================================================================
	def mprintf(self, text):
		
		self.ui.outputConsole.insertPlainText("\n"+str(text))

		sb = self.ui.outputConsole.verticalScrollBar()
		sb.setValue(sb.maximum())
		self.statusBarMessage.setText(str(text))

	def getUi(self, attrNames):
		if type(attrNames) in (type([]), type(())):
			return tuple(getattr(self.ui, i) for i in attrNames)
		else:
			return getattr(self.ui, attrNames)

	def abs(self, val):
		if self.ui.absOperations.isChecked():
			return abs(val)
		else:
			return val

	def processSelectedData(self, Name, sender):
		'''Застосовувати операції для всіх обраних даних'''
		if self.ui.workWithSelectedData.isChecked():
			self.workWithSelectedData(state=True)
			self.selectedDataDict.pop(Name, None)
			print("selected data:", self.selectedDataDict.keys())
			if len(self.selectedDataDict) >= 1:
				self.nameBox.setCurrentIndex(next(iter(self.selectedDataDict.values())))
				if hasattr(sender(), 'click'):
					sender().click()
				elif hasattr(sender(), 'trigger'):
					sender().trigger()
				else:
					pass

	def workWithSelectedData(self, state=False):
		if state:
			selected = self.ui.namesTable.selectionModel().selectedIndexes()
			for i in selected:
				# rows.append(i.row())
				name = self.ui.namesTable.item(i.row(), 0).text()
				self.selectedDataDict.update({name: i.row()})
			# del self.data[name]['main']
			# print(self.data.keys(), name)
			# names.append(name)

	def getValue(self, names):
		return (getattr(self.ui, i).value() for i in names)

	def setToolsLayer(self):
		name = self.sender().objectName().split('action')[1]
		self.ui.stackedWidget.setCurrentWidget(self.getUi('page_' + name))
	
	def closeEvent(self, QCloseEvent):
		print("Close...")
		guisave(self.ui, self.settings)
		sys.exit()
		#QCloseEvent.accept()
		
	"""
	def changeEvent(self,event):
		if(event.type()==QtCore.QEvent.WindowStateChange):
			print("QtCore.QEvent.WindowStateChange")
		#if self.isMinimized():

	def eventFilter(self, source, event):
		if (event.type() == QtCore.QEvent.WindowStateChange and
			source is self.ui):
			pos = event.exit()
			print('mouse move: (%d, %d)' % (pos.x(), pos.y()))
		return QWidget.eventFilter(self, source, event)
	"""
	def uiConnect(self):
		'''Пов’язвння сигналів з слотами'''

		##############  Filters	###############################################
		self.ui.FiltOk.clicked.connect(self.setFilters)

		##############  ReHi3	  ###############################################
		self.ui.reHi3_ok.clicked.connect(self.recalcReHi3)
		##############  ImHi3	  ###############################################
		self.ui.imHi3_ok.clicked.connect(self.recalcImHi3)
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
		# self.ui.AutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		# self.ui.AutoB_splineS.toggled[bool].connect(self.connectAutoB_sS)

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
		self.ui.joinDataArrays.clicked.connect(self.joinDataArrays)
		# self.ui.workWithSelectedData.toggled[bool].connect(self.workWithSelectedData)
		# Усереднення для N імпульсів при певному положенні клину
		self.ui.startStepAverage.toggled.connect(self.ui.startStepAverage_N.setEnabled)
		##########################################################################



		self.ui.Undo.triggered.connect(self.undoData)
		self.ui.Reset.triggered.connect(self.resetData)
		self.ui.Undo.triggered.connect(self.setPrevScale)
		self.ui.Reset.triggered.connect(self.setPrevScale)

		self.ui.tmpShow.toggled[bool].connect(self.plotTmp)
		self.ui.autoScale.toggled[bool].connect(self.set_autoScale)

		# self.ui.processView.toggled[bool].connect(self.processView)
		self.ui.actionProcessView.toggled[bool].connect(self.processView)
		self.ui.actionDublicateData.triggered.connect(self.dublicateData)

		## norm
		self.ui.norm_Max.triggered.connect(self.norm_Max)
		self.ui.norm_Point.toggled[bool].connect(self.norm_Point)
		self.ui.norm_FirstPoint.triggered.connect(self.norm_FirstPoint)
		self.ui.norm_Shift0.triggered.connect(self.norm_Shift0)
		self.ui.norm_Shift0X.triggered.connect(self.norm_Shift0X)
		self.ui.norm_Shift0Xh.triggered[bool].connect(self.norm_Shift0Xh)
		self.ui.norm_ShiftRange.triggered[bool].connect(self.norm_ShiftRange)
		self.ui.norm_AtX.triggered.connect(self.norm_AtX)
		self.ui.ShiftXY.clicked.connect(self.ShiftXY)


		# self.ui.settings.triggered.connect(self.settings.show)
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
		self.ui.action_find2Tangent.toggled[bool].connect(self.find_2Tangent)

		## Інтенсивність
		self.ui.recalcAi2.clicked.connect(self.recalcAi2)
		self.ui.recalcIntensResult.clicked.connect(self.recalcIntensResult)
		self.ui.calibrCoefFromFiles.clicked.connect(self.calibrCoefFromFiles)

		self.ui.movePoint.triggered.connect(self.movePoint)
		self.ui.flipData.triggered.connect(self.flipData)

		self.ui.actionSaveAll.triggered.connect(self.saveAll)
		self.ui.actionSaveProject.triggered.connect(self.saveProject)
		self.ui.actionOpenProject.triggered.connect(self.openProject)
		#self.connect(self.ui, QtCore.SIGNAL('destroyed(QObject *)'), self.closeEvent) 
		self.ui.Close.triggered.connect(self.closeEvent)
		'''
		#self.ui.rYInPercents.toggled[bool].connect(self.rYInPercents)

		self.ui.Close.triggered.connect(self.close)
		#
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
		self.ui.actionImHi3.triggered.connect(self.setToolsLayer)
		self.ui.actionFilters.triggered.connect(self.setToolsLayer)
		self.ui.actionIntens.triggered.connect(self.setToolsLayer)

		self.ui.actionDataDock.triggered.connect(self.ui.DataDock.show)


def main():
	signal.signal(signal.SIGINT, signal.SIG_DFL)  # Застосування Ctrl+C в терміналі

	app = QtWidgets.QApplication(sys.argv)
	win = QTR()

	sys.exit(app.exec_())


if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')
	main()

