#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
import sys, os
from PyQt4 import QtGui, QtCore, uic
import scipy as sp
from scipy.signal import medfilt
import glue_designer2 as qcut
from form import Ui_MainWindow

import signal

class Array(sp.ndarray):

	def __new__(cls, input_array, scale=[None,None], Type = None):
		# Input array is an already formed ndarray instance
		# We first cast to be our class type
		obj = sp.asarray(input_array).view(cls)
		# add the new attribute to the created instance
		obj.scale = scale
		obj.Type = Type
		# Finally, we must return the newly created object:
		return obj

	def __array_finalize__(self, obj):
		# see InfoArray.__array_finalize__ for comments
		if obj is None: return
		self.scale = getattr(obj, 'scale', [None,None])
		self.Type = getattr(obj, 'Type', None)
	
class QTR(QtGui.QMainWindow):
	''' Ініціалізація змінних.
	cXXXXXX	-	змінна, що відповідає кросу
	sXXXXXX	-	змінна, що відповідає зразку
	rXXXXXX	-	змінна, що відповідає результату
	
	Індексація:
	0 - крос
	1 - зразок
	2 - результат
	'''
	Path = ['','','']
	Root = os.getcwd()
	FiltersPath = "./filters.csv"
	# Кортеж історії змін. Містить списки з типом масштабу та масивами даних
	# ( [масив даних, [тип масштабу по Х, тип масштабу по Y]])
	filtersDict = {}
	filtList = ([1.,1.],[1.,1.])
	LENGTH = b"1064"
	dataStack = (
		[Array(sp.zeros((0,2)), scale=[0,0], Type = 0)],
		[Array(sp.zeros((0,2)), scale=[0,0], Type = 1)],
		[Array(sp.zeros((0,2)), scale=[0,0], Type = 2)] )
	# DataUpdated signal -> slot
	data_signal = QtCore.pyqtSignal(int, name = "dataChanged")
	
	def __init__(self):
		super(QTR, self).__init__()
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.fileDialog = QtGui.QFileDialog(self)
		
		self.qcut = qcut.DesignerMainWindow()
		#QtCore.QObject.connect( self.qcut.mplactionSave, QtCore.SIGNAL('triggered()'), self.getBackFromQcut)
		self.qcut.dataChanged.connect(self.getBackFromQcut)
		self.qcut.show()
		##### Signals -> Slots #########################################
		
		self.uiConnect()
		
	####################################################################
	########################  Обробка  #################################
	####################################################################
	def poly_cut(self, data, p, d=0.7, m=6, precision = 0.80):
		'''	Обрізка вздовж кривої апроксиміції поліномом.
		m	-	степінь полінома
		p	-	ширина смуги
		d	-	коефіцієнт уширення
		'''
		X, Y = data[:,0], data[:,1]
		t = True
		fringe = []
		while t:
			EQ = sp.poly1d( sp.polyfit(X, Y, m) )
			poly_Y = EQ( X )
			condition = ((abs(Y - poly_Y)<(p * ( d + abs(poly_Y/max(poly_Y))))))!=0
			fringe.append(sp.std(abs(Y - poly_Y)))
			print(sp.std(abs(Y - poly_Y)), p * ( d + abs(poly_Y/max(poly_Y))))
			Y = Y[ condition ]
			X = X[ condition ]
			t = ((fringe[-1]/fringe[0])>=precision)
			if precision == 0:
				break
			print(t,fringe[-1]/fringe[0])
			d *= 0.95
			p *= 0.95
		return Array(sp.array([X, Y]).T, Type = data.Type, scale = data.scale)
		
	def averaging(self, data, xi = [], Start = 1, End = 2, Step = 1):
		'''	Усереднення між заданими вузлами.
				
		'''
		x, y = data[:,0], data[:,1]
		if not any(xi):
			xi = sp.arange(Start, End,Step)
		else:
			xi = sp.sort(xi)
		xi_1 = sp.insert(xi,-1,xi[-1])
		EQ = sp.poly1d( sp.polyfit(x, y, 3) )
		ynew = []
		for i in range(len(xi_1)-1):
			window = ( (x>=xi_1[i]) * (x<xi_1[i+1]) )!=0
			y_w = y[window]
			if y_w.any():		
				ynew.append(sp.mean(y_w))
			else: 
				if i != 0 and i>3:
					ynew.append(  sp.mean(sp.array([EQ(xi_1[i])] + ynew[-2:])))
				else:
					ynew.append(EQ(xi_1[i]))	
	
		return Array(sp.array([xi, sp.array(ynew)]).T, Type = data.Type, scale = data.scale)
		
	def b_s(self, data, xi = [], Start = 1, End = 2, Step = 1, sm = 1100000., km = 5):
		'''	Інтерполяція B-сплайном
		sm	-	коефіцієнт згладжування
		km	-	степінь полінома
		'''
		print("B-spline interpolation [s = %.3f, k = %.3f]" % (sm,km))
		x, y = data[:,0], data[:,1]
		if not any(xi):
			xi = sp.arange(Start, End,Step)
		y_interp = sp.interpolate.UnivariateSpline(x, y, s = sm, k = km)(xi)
		return Array(sp.array([xi, y_interp]).T, Type = data.Type, scale = data.scale)
	####################################################################
	########################  Слоти  ###################################
	####################################################################
	def Save(self):
		Dict = {'cSave' : 0, 'sSave' : 1, 'rSave' : 2}
		senderName = self.sender().objectName()
		active = Dict[senderName]
		data = self.getData(active)
		filename = QtGui.QFileDialog.getSaveFileName(self,'Save File', self.Root)
		if filename:
			sp.savetxt(str(filename), data)
	
	def AutoB_splineS(self, state, isSignal = True, senderType = 0, param = 0.95):
		Dict = {
			'cAutoB_splineS' : (0, self.ui.cB_splineS,  self.ui.cB_splineStep, self.ui.cB_splineK),
			'sAutoB_splineS' : (1, self.ui.sB_splineS,  self.ui.sB_splineStep, self.ui.sB_splineK),
			'rAutoB_splineS' : (2, self.ui.rB_splineS,  self.ui.rB_splineStep, self.ui.rB_splineK)}
		senderName = ''
		if isSignal:
			senderName = self.sender().objectName()
		else:
			Names = ['c', 's', 'r']
			senderName = Names[senderType]+'AutoB_splineS'
		active = Dict[senderName]
		data = self.getData(active[0])
		if state:
			active[1].setEnabled(False)
			y = data[:,1]
			x = data[:,0]
			EQ = sp.poly1d( sp.polyfit(x, y, 3) )
			poly_Y = EQ( x )
			Y = y - poly_Y
			Step = float(active[2].value())
			K = float(active[3].value())

			try:
				print(str((1+Step/K**3)*param))
				active[1].setValue(sp.std(Y)**2*len(y)*(1+Step/K**2)*param)
			except:
				print("AutoB_splineS: SmoothParamError")
		else:
			active[1].setEnabled(True)
			
	def AutoInterval(self, state, isSignal = True, senderType = 0):
		""" визначаємо мінімальний спільний інтервал по Х"""
		Dict = {
			'cAutoInterval' : (0, self.ui.cStart, self.ui.cEnd),
			'sAutoInterval' : (1, self.ui.sStart, self.ui.sEnd),
			'rAutoInterval' : (2, self.ui.rStart, self.ui.rEnd)}
		senderName = ''
		if isSignal:
			senderName = self.sender().objectName()
		else:
			Names = ['c', 's', 'r']
			senderName = Names[senderType]+'AutoInterval'
		active = Dict[senderName]
		Min, Max = 0, 0
		print('state', state)
		if state and active[0] == 0:
			active[1].setEnabled(False); active[2].setEnabled(False)
			if sp.any(self.getData(1)):
				cMin, cMax = self.getData(0)[:,0].min(), self.getData(0)[:,0].max()
				sMin, sMax = self.getData(1)[:,0].min(), self.getData(1)[:,0].max()
				Max = min(cMax, sMax)
				Min = max(cMin, sMin)
			else: Min, Max = self.getData(0)[:,0].min(), self.getData(0)[:,0].max()
		elif not state and active[0] == 0:
			active[1].setEnabled(True); active[2].setEnabled(True)
		elif state and active[0] == 1:
			active[1].setEnabled(False); active[2].setEnabled(False)
			if sp.any(self.getData(0)):
				cMin, cMax = self.getData(0)[:,0].min(), self.getData(0)[:,0].max()
				sMin, sMax = self.getData(1)[:,0].min(), self.getData(1)[:,0].max()
				Max = min(cMax, sMax)
				Min = max(cMin, sMin)
			else: Min, Max = self.getData(1)[:,0].min(), self.getData(1)[:,0].max()
		elif not state and active[0] == 1:
			active[1].setEnabled(True); active[2].setEnabled(True)
		elif state and sp.any(self.getData(2)):
			active[1].setEnabled(False); active[2].setEnabled(False)
			Min, Max = self.getData(2)[:,0].min(), self.getData(2)[:,0].max()
		elif not state and sp.any(self.getData(2)):
			active[1].setEnabled(True); active[2].setEnabled(True)

		if Max and Min:
			active[1].setValue(Min)
			active[2].setValue(Max)
	
	def ResEval(self):
		""" Обчислюємо результат.
			Якщо розміри масивів не співпадають,
			то усереднюємо довший по вузлах коротшого
		"""
		Param = (	(self.ui.cStart.value(),  self.ui.cEnd.value(), self.ui.cAverageStep.value()),
					(self.ui.sStart.value(),  self.ui.sEnd.value(), self.ui.sAverageStep.value()))
		cData = self.getData(0)
		sData = self.getData(1)
		if cData.scale == [0,0] and sData.scale == [0,0]:
			
			if cData[:,0] != sData[:,0]:
				cLen = cData[:,0].max() - cData[:,0].min()
				sLen = sData[:,0].max() - sData[:,0].min()
				data, xi = [], []
				if cLen >= sLen:
					active = Param[1]
					data = cData
					xi = sData[:,0]
				else:
					active = Param[0]
					data = sData
					xi = cData[:,0]
				data = self.averaging(data,xi = xi, Start = active[0], End = active[1], Step = active[2])
				self.updateData(array = data)
			cData = self.getData(0)
			sData = self.getData(1)
			x = cData[:,0]
			y = sData[:,1]/ cData[:,1]
			self.updateData(array = Array(sp.array([x,y]).T, Type = 2, scale = [0,0]),action = 0)
		else: print('ResEval: scaleError')
			
	def polyCut(self):
		Dict = {'cPolyOk' : (0,self.ui.cPolyP.value(), self.ui.cPolyD.value(), self.ui.cPolyM.value()),
				'sPolyOk' : (1,self.ui.sPolyP.value(), self.ui.sPolyD.value(), self.ui.sPolyM.value())}
		senderName = self.sender().objectName()
		active = Dict[senderName]
		precisionParam = ( self.ui.cPolyPrecision, self.ui.sPolyPrecision)
		Param = 0.
		if precisionParam[active[0]].isEnabled():
			Param = precisionParam[active[0]].value()
		XY = self.getData(active[0])
		data = self.poly_cut(XY, active[1], active[2], active[3], precision = Param)
		self.updateData(array = data)
		
	def Average(self):
		Dict = {'cAverageOk' : (0,self.ui.cStart.value(),  self.ui.cEnd.value(), self.ui.cAverageStep.value()),
				'sAverageOk' : (1,self.ui.sStart.value(),  self.ui.sEnd.value(), self.ui.sAverageStep.value())}
		senderName = self.sender().objectName()
		active = Dict[senderName]
		XY = self.getData(active[0])
		data = self.averaging(XY, Start = active[1], End = active[2], Step = active[3] )
		self.updateData(array = data)
		
	def medFilt(self):
		Dict = {'cMedFilt' : (0,self.ui.cMedFiltS.value()),
				'sMedFilt' : (1,self.ui.sMedFiltS.value()),
				'rMedFilt' : (2,self.ui.rMedFiltS.value())	}
		senderName = self.sender().objectName()
		active = Dict[senderName]
		XY = self.getData(active[0])
		y = medfilt(XY[:,1], kernel_size = active[1])
		self.updateData(array = Array(sp.array([XY[:,0], y]).T, Type = XY.Type, scale = XY.scale))
	
	def B_spline(self):
		Dict = {
			'cB_splineOk' : (0,self.ui.cStart.value(), self.ui.cEnd.value(), self.ui.cB_splineStep.value(),
				self.ui.cB_splineS.value(), self.ui.cB_splineK.value()),
			'sB_splineOk' : (1,self.ui.sStart.value(), self.ui.sEnd.value(), self.ui.sB_splineStep.value(),
				self.ui.sB_splineS.value(), self.ui.sB_splineK.value()),
			'rB_splineOk' : (2,self.ui.rStart.value(), self.ui.rEnd.value(), self.ui.rB_splineStep.value(),
				self.ui.rB_splineS.value(), self.ui.rB_splineK.value())
					}
		senderName = self.sender().objectName()
		active = Dict[senderName]
		XY = self.getData(active[0])
		data = self.b_s(XY, Start = active[1], End = active[2], Step = active[3], sm = active[4], km = active[5])
		self.updateData(array  = data)
		
	def setLogScale(self, state):

		
		Dict = {
			'c' : (0, [int(bool(self.ui.cXLogScale.checkState())),int(bool(self.ui.cYLogScale.checkState()))]),
			's' : (1, [int(bool(self.ui.sXLogScale.checkState())),int(bool(self.ui.sYLogScale.checkState()))]),
			'r' : (2, [int(bool(self.ui.rXLogScale.checkState())),int(bool(self.ui.rYLogScale.checkState()))]),
				}
		senderName = self.sender().objectName()
		key = senderName[0]
		active = Dict[key]
		tempLogScale = active[1]
		data = self.getData(active[0])
		xy = data.copy()
		Scale = xy.scale

		for i in (0,1):
			if Scale[i] != tempLogScale[i]:
				if tempLogScale[i] == 1:
					xy[:,i] = sp.log10(data[:,i])
				else:
					xy[:,i] = sp.power(10.,data[:,i])
				Scale[i] = int(tempLogScale[i])

		self.updateData(array = Array(xy, scale = tempLogScale, Type = data.Type))
		
	def Undo(self):
		Dict = {'cUndo' : (0,self.ui.cUndo), 'sUndo' : (1,self.ui.sUndo), 'rUndo' : (2,self.ui.rUndo)}
		senderName = self.sender().objectName()
		if len(self.dataStack[Dict[senderName][0]])>=2:
			Type = Dict[senderName][0]
			self.updateData(Type = Type, action = -1)
			
		else:
			Dict[senderName][1].setEnabled(False)
			
	def Reset(self):
		Dict = {'cReset' : (0,self.ui.cReset), 'sReset' : (1,self.ui.sReset), 'rReset' : (2,self.ui.rReset)}
		senderName = self.sender().objectName()
		if len(self.dataStack[Dict[senderName][0]])>=2:
			Type = Dict[senderName][0]
			self.updateData(Type = Type, action = 0)
			
		else: Dict[senderName][1].setEnabled(False)
		
	# Plot current tab
	def plotCurrent(self, index):
		if index > 0:
			Type = index-1
			if sp.any(self.getData(Type)):
				active = self.getData(Type);
				if not self.qcut.isVisible():
					self.qcut.setVisible(True)
				else: pass
				self.Plot(active)
			else: pass
		else: pass
		
	def getBackFromQcut(self):
		''' Отримання даних, що змінені вручну в QCut'''
		print( "QCut -> "+str(sp.shape(self.qcut.tdata)), self.qcut.tdata.Type, self.qcut.tdata.scale)
		data, Type, scale = self.qcut.getData()
		self.updateData( array = Array(data,  scale=scale, Type = Type))
		
	def pathTextChanged(self, text):
		"""Якщо поле з шляхом до файлу для завантаження було змінене"""
		Dict = {'cPath' : (0, self.ui.cLoad), 'sPath' : (1, self.ui.sLoad)}
		sender = self.sender()
		active = Dict[sender.objectName()]
		
		if os.path.exists(str(sender.text())):
			self.Path[active[0]] = str(sender.text())
			if not active[1].isEnabled():
				active[1].setEnabled(True)
		else: active[1].setEnabled(False)
		
	def getFilePath(self):
		'''Вибір файлу для завантаження'''
		Dict = {'cFile' : (0, self.ui.cPath, self.ui.cLoad), 'sFile' : (1, self.ui.sPath, self.ui.sLoad)}
		senderName = self.sender().objectName()
		active = Dict[senderName]
		
		path = str(self.fileDialog.getOpenFileName(self,'Open File', self.Root))
		if path:
			self.Root = os.path.dirname(path)
			self.Path[active[0]] = path
			active[1].setText(self.Path[active[0]])
			active[2].setEnabled(True)
			
	def loadData(self):
		'''Завантаження даних з файлів'''
		Dict = {"cLoad" : (0, self.ui.cXColumn, self.ui.cYColumn, self.ui.cMColumn, self.ui.cMCheck),\
			"sLoad" : (1, self.ui.sXColumn, self.ui.sYColumn, self.ui.sMColumn, self.ui.sMCheck)}
		Tabs = ( (self.ui.tab_2, self.ui.tab_3,self.ui.tab_4),\
			(self.ui.tab_3, self.ui.tab_2,self.ui.tab_4))
		FiltersKeys = (
			(self.ui.cXFilt,self.ui.cYFilt),
			(self.ui.sXFilt,self.ui.sYFilt)
					)
		senderName = self.sender().objectName()
		active = Dict[senderName]
		data = []
		XY = sp.zeros((0,2))
		path = self.Path[active[0]]
		if os.path.exists(path):
			try:
				data = sp.loadtxt(path)
				activeFilt = FiltersKeys[active[0]]
				filtNames = ''
				
				if activeFilt[0].isEnabled() and activeFilt[1].isEnabled():
					self.filtersDict = self.getFilters(length = self.LENGTH)
					for i in (0,1):
						filtNames = activeFilt[i].text().strip().replace(" ","").upper()
						temp = 1.
						
						if filtNames:
							temp = self.resFilters(filtNames)
							
						self.filtList[active[0]][i] = temp
				else:
					self.filtList[active[0]][:] = [1., 1.]
				print("Filters [X,Y]:",self.filtList[active[0]])
				xc = active[1].value()
				yc = active[2].value()
				mc = active[3].value()
				if active[4].checkState():
					XY = sp.array( [data[:,xc], data[:,yc] ]).T / sp.array([data[:,mc], data[:,mc]]).T
				else:
					XY = sp.array( [data[:,xc], data[:,yc] ]).T
				XY = XY[XY[:,0] > 0]
				XY = XY[sp.argsort(XY[:,0])]
				XY[:,0] = XY[:,0]/self.filtList[active[0]][0]
				XY[:,1] = XY[:,1]/self.filtList[active[0]][1]
				self.updateData(array = Array(XY,scale=[0,0],Type = active[0]), action = 0)
				Tabs[active[0]][0].setEnabled(True)
				if Tabs[active[0]][1].isEnabled():
					Tabs[active[0]][2].setEnabled(True)
			except (ValueError, IOError, IndexError):
				print("loadData: readError")
		else: print('loadData: pathError')
			
	def dataListener(self,Type):
		"""Обробка зміни даних"""
		Buttons = ( (self.ui.cUndo, self.ui.cReset), (self.ui.sUndo, self.ui.sReset),
			(self.ui.rUndo, self.ui.rReset))
		active = self.getData(Type)
		print("dataChanged: scaleX : %d, scaleY : %s, type : %d, len : %d" %\
			  (active.scale[0],active.scale[1],active.Type, sp.shape(active)[0]))
		#for i in self.dataStack[Type]:
		#	print(i.scale)
		
		if sp.any(active):
			intervalCheck = [self.ui.cAutoInterval, self.ui.sAutoInterval, self.ui.rAutoInterval]
			b_splineSCheck = [self.ui.cAutoB_splineS, self.ui.sAutoB_splineS, self.ui.rAutoB_splineS]
			self.AutoInterval(intervalCheck[Type].checkState(), isSignal = False, senderType = Type)
			self.AutoB_splineS(b_splineSCheck[Type].checkState(), isSignal = False, senderType = Type )
			##### Undo/Reset
			hist = self.dataStack[Type]
			state = False
			if len(hist)>=2:
				state = True
			Buttons[Type][0].setEnabled(state)
			Buttons[Type][1].setEnabled(state)
	
	def lengthChange(self, text):
		if text:
			self.LENGTH = text.strip().encode('utf-8')
		else: print("lengthChange: LengthError")
	####################################################################
	########################  Допоміжні методи  ########################
	####################################################################
	def Plot(self, array):
		self.qcut.Plot(array)
		#self.inQcut = [Type, array.scale]
	def updateData(self, array = Array(sp.zeros((0,2)),scale=[0,0], Type = 0), action = 1, Type = None):
		""" Запис в тимчасовий файл даних з масиву
		action = {-1, 0, 1, 2}
			-1	:	undo
			0	:	reset
			1	:	add
		logScale = [isLogX, isLogY]
		"""
		
		if Type is None:
			if sp.any(array):
				Type = array.Type
				print(sp.shape(array),array.Type)
		
		emit = False
		#print(len(self.dataStack[Type]),action)
		if action == 1:
			if sp.any(array) and sp.shape(array)[1] == 2 and sp.shape(array)[0] > 1:
				self.dataStack[Type].append(array)
				emit = True

			else: print('updateData: arrayError',sp.any(array) , sp.shape(array)[1] == 2 , sp.shape(array)[0] > 1)
			
		elif action == -1 and len(self.dataStack[Type])>=2:
			self.dataStack[Type].pop()
			emit = True
			self.setActiveLogScale(Type = Type, scale = self.getData(Type).scale)
		elif action == 0:
			if sp.any(array) and sp.shape(array)[1] == 2 and sp.shape(array)[0] > 1 and len(self.dataStack[Type])>=1:
				""" Тут можна спробувати замінити:
				while len(self.dataStack[Type])>=1:
					self.dataStack[Type].pop()
				на
					self.dataStack[Type][1:] = []
				
				"""
				#while len(self.dataStack[Type])>=1:
				#	self.dataStack[Type].pop()
				self.dataStack[Type][0:] = []
				self.dataStack[Type].append(array)
				emit = True
			if not sp.any(array) and len(self.dataStack[Type])>=2:
				#while len(self.dataStack[Type])>=2:
				#	self.dataStack[Type].pop()
				self.dataStack[Type][1:] = []
				emit = True
				self.setActiveLogScale(Type = Type, scale = self.getData(Type).scale)
		else:
			print("updateData: Error0",len(self.dataStack[Type]))
			print(sp.shape(self.getData(Type)))
		if emit:
			self.data_signal.emit(Type)
			self.Plot(self.getData(Type) )
			
			
	def setActiveLogScale(self,scale = [0,0], Type = 0):
		LogScale = (
			(self.ui.cXLogScale, self.ui.cYLogScale),
			(self.ui.sXLogScale, self.ui.sYLogScale),
			(self.ui.rXLogScale, self.ui.rYLogScale))
		tmp = LogScale[Type]
		print(bool(scale[0]),bool(scale[1]))
		tmp[0].stateChanged[int].disconnect(self.setLogScale)
		tmp[1].stateChanged[int].disconnect(self.setLogScale)
		tmp[0].setChecked(scale[0]*2)
		tmp[1].setChecked(scale[1]*2)
		tmp[0].stateChanged[int].connect(self.setLogScale)
		tmp[1].stateChanged[int].connect(self.setLogScale)

			
	def getData(self,Type): return self.dataStack[Type][-1]
	
	def getFilters(self, length="532"):
		"""Читання таблиці фільтрів та вибір значень для даної довжини хвилі"""
		filt = sp.loadtxt(self.FiltersPath, dtype="S")
		col = sp.where(filt[0,:]==length)[0][0]
		return dict( zip(filt[1:,0], sp.array(filt[1:,col],dtype="f") ) )
	
	def resFilters(self,filters):
		"""Перерахунок для різних комбінацій фільтрів"""
		return  sp.multiply.reduce( [ self.filtersDict[i.encode('utf-8')] for i in filters.split(",")] )
	
	def uiConnect(self):
		self.ui.cFile.clicked.connect(self.getFilePath)
		self.ui.sFile.clicked.connect(self.getFilePath)
		self.ui.cLoad.clicked.connect(self.loadData)
		self.ui.sLoad.clicked.connect(self.loadData)
		self.ui.cPath.textChanged.connect(self.pathTextChanged)
		self.ui.sPath.textChanged.connect(self.pathTextChanged)
		self.ui.tabWidget.currentChanged[int].connect(self.plotCurrent)
		self.ui.cMCheck.stateChanged.connect(self.ui.cMColumn.setEnabled)
		self.ui.sMCheck.stateChanged.connect(self.ui.sMColumn.setEnabled)
		self.ui.cUndo.clicked.connect(self.Undo)
		self.ui.sUndo.clicked.connect(self.Undo)
		self.ui.rUndo.clicked.connect(self.Undo)
		self.ui.cReset.clicked.connect(self.Reset)
		self.ui.sReset.clicked.connect(self.Reset)
		self.ui.rReset.clicked.connect(self.Reset)
		self.ui.cXLogScale.stateChanged[int].connect(self.setLogScale)
		self.ui.cYLogScale.stateChanged[int].connect(self.setLogScale)
		self.ui.sXLogScale.stateChanged[int].connect(self.setLogScale)
		self.ui.sYLogScale.stateChanged[int].connect(self.setLogScale)
		self.ui.rXLogScale.stateChanged[int].connect(self.setLogScale)
		self.ui.rYLogScale.stateChanged[int].connect(self.setLogScale)
		self.ui.cPolyOk.clicked.connect(self.polyCut)
		self.ui.sPolyOk.clicked.connect(self.polyCut)
		self.ui.cAverageOk.clicked.connect(self.Average)
		self.ui.sAverageOk.clicked.connect(self.Average)
		self.ui.cMedFilt.clicked.connect(self.medFilt)
		self.ui.sMedFilt.clicked.connect(self.medFilt)
		self.ui.rMedFilt.clicked.connect(self.medFilt)
		self.ui.cB_splineOk.clicked.connect(self.B_spline)
		self.ui.sB_splineOk.clicked.connect(self.B_spline)
		self.ui.rB_splineOk.clicked.connect(self.B_spline)
		self.ui.rButton.clicked.connect(self.ResEval)
		self.ui.cAutoInterval.stateChanged[int].connect(self.AutoInterval)
		self.ui.sAutoInterval.stateChanged[int].connect(self.AutoInterval)
		self.ui.rAutoInterval.stateChanged[int].connect(self.AutoInterval)
		self.ui.cAutoB_splineS.stateChanged[int].connect(self.AutoB_splineS)
		self.ui.sAutoB_splineS.stateChanged[int].connect(self.AutoB_splineS)
		self.ui.rAutoB_splineS.stateChanged[int].connect(self.AutoB_splineS)
		self.ui.cSave.clicked.connect(self.Save)
		self.ui.sSave.clicked.connect(self.Save)
		self.ui.rSave.clicked.connect(self.Save)
		self.ui.LENGTH.textChanged[str].connect(self.lengthChange)
		self.ui.cFilt.stateChanged[int].connect(self.ui.cXFilt.setEnabled)
		self.ui.cFilt.stateChanged[int].connect(self.ui.cYFilt.setEnabled)
		self.ui.sFilt.stateChanged[int].connect(self.ui.sXFilt.setEnabled)
		self.ui.sFilt.stateChanged[int].connect(self.ui.sYFilt.setEnabled)
		self.ui.cAutoPoly.stateChanged[int].connect(self.ui.cPolyPrecision.setEnabled)
		self.ui.sAutoPoly.stateChanged[int].connect(self.ui.sPolyPrecision.setEnabled)
		#________________________________________________
		self.data_signal[int].connect(self.dataListener)
	
if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	app = QtGui.QApplication(sys.argv)
	win = QTR()
	win.show()
	sys.exit(app.exec_())