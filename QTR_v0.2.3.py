#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
import sys, os, signal
from PyQt4 import QtGui, QtCore, uic
import scipy as sp
from scipy.signal import medfilt
import glue_designer as qcut
from form import Ui_MainWindow

# Масив даних, що буде містити дані, їх масштаб та тип
class Array(sp.ndarray):
	
	def __new__(cls, input_array, scale=[0,0], Type = None):
		# Input array is an already formed ndarray instance
		# We first cast to be our class type
		obj = sp.asarray(input_array).view(cls)
		# add the new attribute to the created instance
		obj.Type = Type
		obj.scaleX = scale[0]
		obj.scaleY = scale[1]
		obj.scale = scale
		#setattr(obj, 'scale', scale)
		#obj.scale = sp.array([obj.scaleX, obj.scaleY])
		# Finally, we must return the newly created object:
		return obj
	def __array_finalize__(self, obj):
		# see InfoArray.__array_finalize__ for comments
		
		if obj is None: return
		self.Type = getattr(obj, 'Type', None)
		self.scaleX= getattr(obj, 'scaleX', None)
		self.scaleY = getattr(obj, 'scaleY', None)
		self.scale = getattr(obj, 'scale', None)
		#self.scale = self.Scale()
	def Scale(self): return [self.scaleX, self.scaleY]


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
	Path = ['','','']				# Шляхи до файлів
	Root = os.getcwd()				# Поточний каталог
	FiltersPath = os.path.join(os.getcwd(),"filters.csv")	# База фільтрів

	filtersDict = {}				# Словник фільтрів
	filtList = ([1.,1.],[1.,1.])	# Поточні фільтри
	LENGTH = b"1064"				# Довжина хвилі за замовчуванням
	# Стек історії для кроса. зразка і результата
	dataStack = (
		[Array(sp.zeros((0,2)), Type = 0, scale=[0,0])],
		[Array(sp.zeros((0,2)), Type = 1, scale=[0,0])],
		[Array(sp.zeros((0,2)), Type = 2, scale=[0,0])] )
	
	
	
	# DataUpdated signal -> slot
	# Сигнал про зміну в даних
	data_signal = QtCore.pyqtSignal(int, int, name = "dataChanged")
	
	def __init__(self):
		super(QTR, self).__init__()
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		
		self.fileDialog = QtGui.QFileDialog(self)
		
		self.qcut = qcut.DesignerMainWindow()
		# Відкат даних із QCut
		self.qcut.dataChanged.connect(self.getBackFromQcut)
		self.qcut.show()
		
		self.ui.tab_2.setEnabled(False)
		self.ui.tab_3.setEnabled(False)
		self.ui.tab_4.setEnabled(False)
		QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, self.close)
		##### Signals -> Slots #########################################
		self.uiConnect()
	
	# Пошук однотипних об’єктів графічної форми за кортежем імен
	def findChilds(self,obj,names, p = ''):
		'''Додатковий механізм пошуку об’єктів графічної форми
		p	-	атрибут який повертається для кожного елемента
		'''
		if p == 'value': return tuple(self.findChild(obj,name).value() for name in names)
		elif p == 'checkState': return tuple(self.findChild(obj,name).checkState() for name in names)
		else: return tuple(self.findChild(obj,name) for name in names)
	def findUi(self, names): return [ getattr(self.ui, i) for i in names ]
	####################################################################
	########################  Обробка  #################################
	####################################################################
	
	# Механічна обрізка
	def poly_cut(self, data, Start = None, End = None, N = 10, m = 4, p = 0.80):
		'''	Обрізка вздовж кривої апроксиміції поліномом.
		m	-	степінь полінома
		p	-	відсоток від максимального викиду
		N	-	кількість вузлів	
		'''
		X, Y = data[:,0], data[:,1]
		#Обрізка в заданих межах
		if not Start is None:
			if 0 < Start < X.max():
				X, Y = X[X >= Start], Y[X >= Start]
		if not End is None:
			if 0 < End <= X.max():
				X, Y = X[X <= End], Y[X <= End]
		n = int(N)
		EQ = sp.poly1d( sp.polyfit(X, Y, m) )
		poly_Y = EQ( X )
		xnew, ynew = [], []
		Range = range(0,len(X),n)
		i = 0
		for j in list(Range[1:])+[len(X)-1]:
			if j-i<=1: break
			x_temp = X[i:j]
			y_temp = Y[i:j]
			polyY_temp = poly_Y[i:j]
			t = True
			y_old = y_temp - polyY_temp
			std = sp.std(y_old)
			window = []
			width = 0
			for count in range(400):
				width = ( abs(y_old).max()*p )
				window.append( abs(y_old) < width)
				y_new = y_old[window[-1]]
				t = ((sp.std(y_new)/std) >= p)
				y_old = y_new
				if not t: break
				
			for i in window:	x_temp, y_temp = x_temp[i], y_temp[i]
			xnew = xnew + x_temp.tolist()
			ynew = ynew + (y_temp).tolist()
			i = j
		X, Y = xnew, ynew
		return Array(sp.array([X, Y]).T, Type = data.Type, scale = data.scale)
	
	# Усереднення
	def averaging(self, data, Start = None, End = None, N = 1, m = 3):
		'''	Усереднення між заданими вузлами.
		m		-	порядок полінома
		Step	-	кількість вузлів
		'''
		x, y = data[:,0], data[:,1]
		#Обрізка в заданих межах
		if not Start is None:
			if 0 < Start < x.max():
				x, y = x[x >= Start], y[x >= Start]
		if not End is None:
			if 0 < End <= x.max():
				x, y = x[x <= End], y[x <= End]
		
		n = int(N)
		EQ = sp.poly1d( sp.polyfit(x, y, m) )
		poly_Y = EQ( x )
		Range = range(0,len(x),n)
		i = 0
		xnew, ynew = [], []
		for j in list(Range[1:])+[len(x)-1]:
			if j-i <=1:	break
			x_temp = x[i:j].mean()
			xnew.append(x_temp)
			ynew.append( (y[i:j] - poly_Y[i:j]).mean() + EQ(x_temp))
			i = j
		return Array(sp.array([xnew, ynew]).T, Type = data.Type, scale = data.scale)
	
	# Інтерполяція b-сплайном
	def b_s(self, data, xi = [], Start = None, End = None, Step = 1, sm = 1100000., km = 5):
		'''	Інтерполяція B-сплайном
		sm	-	коефіцієнт згладжування
		km	-	степінь полінома
		'''
		
		print("B-spline interpolation [s = %.3f, k = %.3f]" % (sm,km))
		x, y = data[:,0], data[:,1]
		#Обрізка в заданих межах
		if not Start is None:
			if 0 < Start < x.max():
				x, y = x[x >= Start], y[x >= Start]
		if not End is None:
			if 0 < End <= x.max():
				x, y = x[x <= End], y[x <= End]
				
		if not any(xi):
			xi = sp.arange(Start, End,Step)
		y_interp = sp.interpolate.UnivariateSpline(x, y, s = sm, k = km)(xi)
		return Array(sp.array([xi, y_interp]).T,Type = data.Type, scale = data.scale)
	####################################################################
	########################  Слоти  ###################################
	####################################################################
	
	# Повернути масштаб при поверненні в історії
	def setPrevScale(self, Type, action):
		Names = ( 'Y_XScale', 'XLogScale', 'YLogScale', 'LogScale' )
		Types = ('c', 's', 'r')
		if action == 0 or action == -1:
			data = self.getData(Type)
			scale = data.Scale()
			ui_obj = self.findUi(( Types[Type] + i for i in Names))
			for t in ui_obj[:-1]:
				t.toggled[bool].disconnect(self.setNewScale)			
			if scale[1] == 2:
				ui_obj[0].setChecked(True)
			else:
				ui_obj[0].setChecked(False)
				ui_obj[1].setChecked(scale[0])
				ui_obj[2].setChecked(scale[1])
			
			ui_obj[0].setEnabled(scale == [0,0])
			ui_obj[3].setEnabled((scale == [0,0]) or 1 in scale )
				
			for t in ui_obj[:-1]:
				t.toggled[bool].connect(self.setNewScale)
		else: pass
		
	# Змінити масштаб на новий
	def setNewScale(self, state):
		Names = ( 'Y_XScale', 'XLogScale', 'YLogScale' )
		Types = {'c' : 0, 's' : 1, 'r' : 2} 
		senderName = self.sender().objectName()
		t, Type = senderName[0], Types[senderName[0]]
		data = self.getData(Type)
		Scale = data.Scale()
		if senderName[1:] == Names[0]:
			ui_obj = getattr(self.ui, t + "LogScale")
			if state:
				Scale[1] = 2
				data[:,1] = data[:,1] / data[:,0]
			else:
				Scale[1] = 0
				data[:,1] = data[:,1] * data[:,0]
			ui_obj.setEnabled(not state)
		else:
			index = bool(senderName[1] != "X")
			ui_obj = getattr(self.ui, t + Names[0])
			if Scale[index] != state:
				if state == 1:
					data[:,index] = sp.log10(data[:,index])
				else:
					data[:,index] = sp.power(10.,data[:,index])
				Scale[index] = int(state)
				ui_obj.setEnabled(Scale == [0,0])
		self.updateData(array = Array(data, Type = Type, scale = Scale))
		
	
			
	
	# Для сигналу про зміну типу інтерполяції кроса при обчисленні результату	
	def interpTypeChanged(self,text):
		'''Перевірка правильності введення типу інтерполяції для обрахунку результату'''
		interpTypes = ('linear', 'nearest', 'zero')#, 'cubic', 'slinear')
		if text.lower().strip().replace(' ','') in interpTypes:
			self.ui.rButton.setEnabled(True)
		else: self.ui.rButton.setEnabled(False)
	
	def Save(self):
		'''Збереження активного масиву до текстового файлу'''
		Dict = {'cSave' : 0, 'sSave' : 1, 'rSave' : 2}
		senderName = self.sender().objectName()
		active = Dict[senderName]
		data = self.getData(active)
		filename = QtGui.QFileDialog.getSaveFileName(self,'Save File', self.Root)
		if filename:
			sp.savetxt(str(filename), data)
	
	def AutoB_splineS(self, state, isSignal = True, senderType = 0, param = 0.95):
		'''Штучний підбір коефіцієнтів для b-сплайн інтерполяції'''
		Dict = {
			'cAutoB_splineS' : (0, 'cB_splineS',  'cB_splineStep', 'cB_splineK'),
			'sAutoB_splineS' : (1, 'sB_splineS',  'sB_splineStep', 'sB_splineK'),
			'rAutoB_splineS' : (2, 'rB_splineS',  'rB_splineStep', 'rB_splineK')}
		senderName = ''
		if isSignal:
			senderName = self.sender().objectName()
		else:
			Names = ['c', 's', 'r']
			senderName = Names[senderType]+'AutoB_splineS'
		active = (Dict[senderName][0],) + self.findChilds(QtGui.QDoubleSpinBox,Dict[senderName][1:])
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
		'''
		Param = (	(self.ui.cStart.value(),  self.ui.cEnd.value(), self.ui.cAverageStep.value()),
					(self.ui.sStart.value(),  self.ui.sEnd.value(), self.ui.sAverageStep.value()))
		'''
		cData = self.getData(0)
		sData = self.getData(1)
		
		if cData.scale == [0,0] and sData.scale == [0,0]:
			
			if self.ui.rButton.isEnabled():
				x = sData[:,0]
				window = (x>=cData[:,0].min())*(x<=cData[:,0].max())
				x = x[window]
				y = sData[:,1]
				y = y[window]
				cY_temp = sp.interpolate.interp1d(cData[:,0], cData[:,1],self.ui.rEvalType.text().lower())(x)
				y = y/ cY_temp
			else: print('ResEval: interpTypeError')
			
			self.updateData(array = Array(sp.array([x,y]).T, Type = 2, scale = [0,0]),action = 0)
		else: print('ResEval: scaleError')
			
	def polyCut(self):
		'''Обрізка [за різними методами]'''
		Dict = {'cPolyOk' : (0,'cPolyN', 'cPolyP', 'cPolyM', 'cStart',  'cEnd'),
				'sPolyOk' : (1,'sPolyN', 'sPolyP', 'sPolyM', 'sStart',  'sEnd')}		
		senderName = self.sender().objectName()
		tmp = Dict[senderName]
		active = (tmp[0],) + self.findChilds(QtGui.QDoubleSpinBox,tmp[1:],p="value")
		XY = self.getData(active[0])
		data = self.poly_cut(XY, N = active[1], p = active[2], m = active[3], Start = active[4], End = active[5])
		self.updateData(array = data.copy())
		
	def Average(self):
		'''Усереднення за різними методами'''
		Dict = {'cAverageOk' : (0,'cStart',  'cEnd', 'cAverageStep'),
				'sAverageOk' : (1,'sStart',  'sEnd', 'sAverageStep')}
		senderName = self.sender().objectName()
		tmp = Dict[senderName]
		active = (tmp[0],) + self.findChilds(QtGui.QDoubleSpinBox,tmp[1:],p="value")
		XY = self.getData(active[0])
		data = self.averaging(XY, Start = active[1], End = active[2], N = active[3] )
		self.updateData(array = data)
		
	def medFilt(self):
		'''Фільтрація медіаною'''
		Dict = {'cMedFilt' : (0,'cMedFiltS'),
				'sMedFilt' : (1,'sMedFiltS'),
				'rMedFilt' : (2,'rMedFiltS')}
		senderName = self.sender().objectName()
		active = (Dict[senderName][0], self.findChild(QtGui.QSpinBox, Dict[senderName][1]).value())
		XY = self.getData(active[0])
		X, Y = XY[:,0], XY[:,1]
		EQ = sp.poly1d( sp.polyfit(X, Y, 4) ) # можна додати прив’язку до степ. поліному 
		poly_Y = EQ( X )
		y_temp = Y - poly_Y
		y = medfilt(y_temp, kernel_size = active[1])
		Y = y + poly_Y
		self.updateData(array = Array(sp.array([XY[:,0], Y]).T, Type = XY.Type, scale = XY.scale))
	
	def B_spline(self):
		'''інтерполяція b-сплайном'''
		Dict = {
			'cB_splineOk' : (0,'cStart', 'cEnd', 'cB_splineStep', 'cB_splineS', 'cB_splineK'),
			'sB_splineOk' : (1,'sStart', 'sEnd', 'sB_splineStep', 'sB_splineS', 'sB_splineK'),
			'rB_splineOk' : (2,'rStart', 'rEnd', 'rB_splineStep', 'rB_splineS', 'rB_splineK')}
		senderName = self.sender().objectName()
		active =  (Dict[senderName][0],) + self.findChilds(QtGui.QDoubleSpinBox, Dict[senderName][1:],p = 'value')
		XY = self.getData(active[0])
		data = self.b_s(XY, Start = active[1], End = active[2], Step = active[3], sm = active[4], km = int(active[5]))
		self.updateData(array  = data)
		
	def Undo(self):
		Dict = {'cUndo' : 0, 'sUndo' : 1, 'rUndo' : 2}
		senderName = self.sender().objectName()
		Type = Dict[senderName]
		if len(self.dataStack[Type])>=2:
			self.updateData(Type = Type, action = -1)
		else:
			self.sender().setEnabled(False)

	def Reset(self):
		Dict = {'cReset' : 0, 'sReset' : 1, 'rReset' : 2}
		senderName = self.sender().objectName()
		Type = Dict[senderName]
		if len(self.dataStack[Type])>=2:
			self.updateData(Type = Type, action = 0)
		else:
			self.sender().setEnabled(False)

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
		data, Type, Scale = self.qcut.getData()
		self.updateData( array = Array(data, Type = Type, scale=Scale)  )
		
	def pathTextChanged(self, text):
		"""Якщо поле з шляхом до файлу для завантаження було змінене"""
		Dict = {'cPath' : (0, 'cLoad'), 'sPath' : (1, 'sLoad')}
		sender = self.sender()
		tmp = Dict[sender.objectName()]
		active = [tmp[0]] + [self.findChild(QtGui.QPushButton,tmp[1])] 
		
		if os.path.exists(str(sender.text())):
			self.Path[active[0]] = str(sender.text())
			if not active[1].isEnabled():
				active[1].setEnabled(True)
		else: active[1].setEnabled(False)
		
	def getFilePath(self):
		'''Вибір файлу для завантаження'''
		Dict = {'cFile' : (0, 'cPath', 'cLoad'), 'sFile' : (1, 'sPath', 'sLoad')}
		senderName = self.sender().objectName()
		tmp = Dict[senderName]
		active = [tmp[0]] + [self.findChild(QtGui.QLineEdit,tmp[1])] + [self.findChild(QtGui.QPushButton,tmp[2])]
		
		path = str(self.fileDialog.getOpenFileName(self,'Open File', self.Root))
		if path:
			self.Root = os.path.dirname(path)
			self.Path[active[0]] = path
			active[1].setText(self.Path[active[0]])
			active[2].setEnabled(True)
			
	def loadData(self):
		'''Завантаження даних з файлів'''
		Dict = {"cLoad" : (0, 'cXColumn', 'cYColumn', 'cMColumn', 'cMCheck','cAutoInterval'),
				"sLoad" : (1, 'sXColumn', 'sYColumn', 'sMColumn', 'sMCheck','sAutoInterval')}
		Tabs = ( ('tab_2', 'tab_3','tab_4'),
			('tab_3', 'tab_2','tab_4'))
		FiltersKeys = (('cXFilt','cYFilt'),	('sXFilt','sYFilt'))
		senderName = self.sender().objectName()
		tmp = Dict[senderName]
		active = (tmp[0],) + self.findChilds(QtGui.QSpinBox,tmp[1:-2]) + self.findChilds(QtGui.QCheckBox,tmp[-2:])
		data = []
		XY = sp.zeros((0,2))
		path = self.Path[active[0]]
		if os.path.exists(path):
			try:
				data = sp.loadtxt(path)
				activeFilt = self.findChilds(QtGui.QLineEdit, FiltersKeys[active[0]])
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
				XY = XY[XY[:,1] > 0]
				XY = XY[sp.argsort(XY[:,0])]
				XY[:,0] = XY[:,0]/self.filtList[active[0]][0]
				XY[:,1] = XY[:,1]/self.filtList[active[0]][1]
				self.updateData(array = Array(XY,Type = active[0]), action = 0)
				tabs = self.findChilds(QtGui.QWidget,Tabs[active[0]])
				tabs[0].setEnabled(True)
				active[5].setChecked(True)
				if tabs[1].isEnabled():
					tabs[2].setEnabled(True)
			except (ValueError, IOError, IndexError):
				print("loadData: readError")
		else: print('loadData: pathError')
			
	def dataListener(self,Type, action):
		"""Обробка зміни даних"""
		Buttons = ( ('cUndo', 'cReset'), ('sUndo', 'sReset'),
			('rUndo', 'rReset'))
		active = self.getData(Type)
		print("dataChanged: scaleX : %d, scaleY : %d, type : %d, len : %d [%d,%d]" %\
			  (active.scaleX, active.scaleY ,active.Type, sp.shape(active)[0],active.scale[0],active.scale[1]))
		#for i in self.dataStack[Type]:
		#	print(i.scale)
		
		if sp.any(active):
			intervalCheck = ['cAutoInterval', 'sAutoInterval', 'rAutoInterval']
			b_splineSCheck = ['cAutoB_splineS', 'sAutoB_splineS', 'rAutoB_splineS']
			intervalObj = self.findChild(QtGui.QCheckBox,intervalCheck[Type])
			b_splineSObj = self.findChild(QtGui.QCheckBox,b_splineSCheck[Type])
			self.AutoInterval(intervalObj.checkState(), isSignal = False, senderType = Type)
			self.AutoB_splineS(b_splineSObj.checkState(), isSignal = False, senderType = Type )
			##### Undo/Reset
			hist = self.dataStack[Type]
			state = False
			if len(hist)>=2:
				state = True
			buttons = self.findChilds(QtGui.QPushButton,Buttons[Type])
			buttons[0].setEnabled(state)
			buttons[1].setEnabled(state)
			
	def closeEvent(self, event):
		self.qcut.close()
	
	def lengthChange(self, text):
		if text:
			self.LENGTH = text.strip().encode('utf-8')
		else: print("lengthChange: LengthError")
	####################################################################
	########################  Допоміжні методи  ########################
	####################################################################
	def Plot(self, array):
		self.qcut.Plot(array)

	def updateData(self, array = Array(sp.zeros((0,2)),scale=[0,0], Type = 0), action = 1, Type = None):
		""" Запис в тимчасовий файл даних з масиву
		action = {-1, 0, 1, 2}
			-1	:	undo
			0	:	reset
			1	:	add
		"""

		if Type is None:
			if sp.any(array):
				Type = array.Type
				#print(sp.shape(array),array.Type)
		
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
			#self.setActiveLogScale( Type)
		elif action == 0:
			print(0)
			if sp.any(array) and sp.shape(array)[1] == 2 and sp.shape(array)[0] > 1 and len(self.dataStack[Type])>=1:
				self.dataStack[Type][0:] = []
				self.dataStack[Type].append(array)
				emit = True
			if not sp.any(array) and len(self.dataStack[Type])>=2:
				self.dataStack[Type][1:] = []
				emit = True
			#self.setActiveLogScale( Type)
			
		else:
			print("updateData: Error0",len(self.dataStack[Type]))
			print(sp.shape(self.getData(Type)))
		try:
			for i in self.dataStack[Type]: print(i.scaleX, i.scaleY, i.shape)
		except:
			pass
		if emit:
			self.data_signal.emit(Type, action)
			self.Plot(self.getData(Type) )
	
	def getData(self,Type): return self.dataStack[Type][-1].copy()
	
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
		self.ui.cMCheck.toggled[bool].connect(self.ui.cMColumn.setEnabled)
		self.ui.sMCheck.toggled[bool].connect(self.ui.sMColumn.setEnabled)
		self.ui.cUndo.clicked.connect(self.Undo)
		self.ui.sUndo.clicked.connect(self.Undo)
		self.ui.rUndo.clicked.connect(self.Undo)
		self.ui.cReset.clicked.connect(self.Reset)
		self.ui.sReset.clicked.connect(self.Reset)
		self.ui.rReset.clicked.connect(self.Reset)
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
		self.ui.cAutoInterval.toggled[bool].connect(self.AutoInterval)
		self.ui.sAutoInterval.toggled[bool].connect(self.AutoInterval)
		self.ui.rAutoInterval.toggled[bool].connect(self.AutoInterval)
		self.ui.cAutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		self.ui.sAutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		self.ui.rAutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		self.ui.cSave.clicked.connect(self.Save)
		self.ui.sSave.clicked.connect(self.Save)
		self.ui.rSave.clicked.connect(self.Save)
		self.ui.LENGTH.textChanged[str].connect(self.lengthChange)
		self.ui.cFilt.toggled[bool].connect(self.ui.cXFilt.setEnabled)
		self.ui.cFilt.toggled[bool].connect(self.ui.cYFilt.setEnabled)
		self.ui.sFilt.toggled[bool].connect(self.ui.sXFilt.setEnabled)
		self.ui.sFilt.toggled[bool].connect(self.ui.sYFilt.setEnabled)
		self.ui.rEvalType.textChanged[str].connect(self.interpTypeChanged)
		
		# Масштабування
		self.ui.cXLogScale.toggled[bool].connect(self.setNewScale)
		self.ui.cYLogScale.toggled[bool].connect(self.setNewScale)
		self.ui.sXLogScale.toggled[bool].connect(self.setNewScale)
		self.ui.sYLogScale.toggled[bool].connect(self.setNewScale)
		self.ui.rXLogScale.toggled[bool].connect(self.setNewScale)
		self.ui.rYLogScale.toggled[bool].connect(self.setNewScale)
		self.ui.cY_XScale.toggled[bool].connect(self.setNewScale)
		self.ui.sY_XScale.toggled[bool].connect(self.setNewScale)
		self.ui.rY_XScale.toggled[bool].connect(self.setNewScale)
		
		#self.close.connect(self.closeEvent)
		#________________________________________________
		self.data_signal[int,int].connect(self.dataListener)
		self.data_signal[int,int].connect(self.setPrevScale)
		
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	def setTool(self,objType, objName): return self.findChild(objType,objName)
	
if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	app = QtGui.QApplication(sys.argv)
	win = QTR()
	win.show()
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	win.setTool(QtGui.QLineEdit,'cPath').setText("/home/kronosua/work/QTR/data/CR4FORWA.TXT")
	win.setTool(QtGui.QLineEdit,'sPath').setText("/home/kronosua/work/QTR/data/SIFORWAR.TXT")
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	
	sys.exit(app.exec_())
	