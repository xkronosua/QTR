#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
import sys, os, signal
from PyQt4 import QtGui, QtCore  #, uic
import scipy as sp
import scipy.interpolate as interp
#from scipy.signal import medfilt
from glue_designer import  DesignerMainWindow
from ui.Ui_form import Ui_MainWindow
from intens import IntensDialog
from settings import SettingsDialog
from createProject import ProjectDialog
import bspline
from console import scriptDialog
from scipy.signal import filtfilt, butter  #lfilter, lfilter_zi
#from setName import NameDialog

#from calibr import CalibrDialog
# Масив даних, що буде містити дані, їх масштаб та тип
class Array(sp.ndarray):
	
	def __new__(cls, input_array, scale=[0,0], Type=0, Name='new'):
		# Input array is an already formed ndarray instan ce
		# We first cast to be our class type
		obj = sp.asarray(input_array).view(cls)
		# add the new attribute to the created instance
		obj.Type = Type
		obj.scaleX = scale[0]
		obj.scaleY = scale[1]
		obj.scale = scale
		obj.Name = Name
		#setattr(obj, 'scale', scale)
		#obj.scale = sp.array([obj.scaleX, obj.scaleY])
		# Finally, we must return the newly created object:
		return obj
	def __array_finalize__(self, obj):
		# see InfoArray.__array_finalize__ for comments
		
		if obj is None: return
		self.Type = getattr(obj, 'Type', None)
		self.Name = getattr(obj, 'Name', None)
		self.scaleX= getattr(obj, 'scaleX', None)
		self.scaleY = getattr(obj, 'scaleY', None)
		self.scale = getattr(obj, 'scale', None)
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
	projects = {}
	Path = ['','','']				# Шляхи до файлів
	Root = os.getcwd()				# Поточний каталог
	FiltersPath = os.path.join(os.getcwd(),"filters.csv")	 # База фільтрів
	Types = {'c': 0, 's': 1, 'r': 2}
	
	
	filtersDict = {}				# Словник фільтрів
	#activeFilters = {}	# Поточні фільтри
	LENGTH = b"1064"				# Довжина хвилі за замовчуванням
	# Стек історії для кроса. зразка і результата
	dataStack = (
		[Array(sp.zeros((0,2)), Type = 0, scale=[0,0])],
		[Array(sp.zeros((0,2)), Type = 1, scale=[0,0])],
		[Array(sp.zeros((0,2)), Type = 2, scale=[0,0])] )
	
	dataDict = {}
	
	showTmp = False		# Показувати проміжні  побудови
	
	tableEditedName = None
	nameEditLock = True
	confDict = dict(
		Scale=[0, 0], 
		Reset=False,
		Undo=False
		)
	dataConfigs = {}
	
	OPT = {	'proc' : False, 
			'defaultTabType' : 0, 
			'projN' : 0
			}

	# DataUpdated signal -> slot
	# Сигнал про зміну в даних
	data_signal = QtCore.pyqtSignal(str, int, name = "dataChanged")
	
	def __init__(self, parent=None):
		super(QTR, self).__init__(parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
		
		## StatusBar
		self.barWaveLen = QtGui.QLabel()
		self.barWaveLen.setObjectName('barWaveLen')
		self.barWaveLen.setText(str(self.LENGTH, 'utf-8'))
		self.ui.statusbar.addPermanentWidget(self.barWaveLen)
		
		self.nameBox = QtGui.QComboBox()
		self.nameBox.setObjectName('fastDataComboBox')
		self.ui.statusbar.addPermanentWidget(self.nameBox)
		
		
		
		self.fileDialog = QtGui.QFileDialog(self)
		
		self.qcut = DesignerMainWindow(parent=self)

		# Відкат даних із QCut
		self.qcut.dataChanged.connect(self.getBackFromQcut)

		self.intensDialog = IntensDialog(parent=self)

		self.settings = SettingsDialog(parent=self)
		self.console = scriptDialog(self)
		
		self.ui.namesTable.setColumnWidth(0,  150);
		self.ui.namesTable.setColumnWidth(1,  20);
		self.ui.namesTable.setColumnWidth(2,  20);
		
		
		self.ui.toolBarGraph.addAction(self.ui.menu_norm.menuAction())
		self.ui.menu_norm.menuAction().setIcon(QtGui.QIcon(':/buttons/ui/buttons/norm_On.png'))
		self.ui.menu_norm.setActiveAction(self.ui.norm_FirstPoint)
		#QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, self.close)
	
		
		
		# Підвантаження таблиці фільтрів
		self.filtersDict = self.getFilters(length = self.LENGTH)
		##### Signals -> Slots #########################################
		self.uiConnect()
		self.activateWindow()
	
	####################################################################
	########################  Обробка  #################################
	####################################################################
	def cutConcatView(self, X, Y, x=None, y=None, state=True):
		''' Обробка видимого/всього діапазону даних '''
		if state:
			Start, End = self.ui.mpl.canvas.ax.get_xlim()
			x, y = X.copy(), Y.copy()
			#Обрізка в заданих межах
			
			if not Start is None:
				if 0 < Start < X.max():
					X, Y = X[X >= Start], Y[X >= Start]
			else: pass  #Start = X.min()
			if not End is None:
				if 0 < End <= X.max():
					X, Y = X[X <= End], Y[X <= End]
			else: pass  #End = X.max()
			return X, Y, x, y
		else:
			less, more = x<X[0], x>X[-1]
			x1, x2 = x[less], x[more]
			y1, y2 = y[less], y[more]
			X, Y = sp.concatenate([x1, X, x2]), sp.concatenate([y1, Y, y2])
			return X, Y
			
	
	def poly_cut(self, data, N=10, m=4,
			p=0.80, AC=False,  discrete=False):
		'''	Обрізка вздовж кривої апроксиміції поліномом.
		m		-	степінь полінома
		p		-	відсоток від максимального викиду
		N		-	кількість вузлів
		AC	-	обробити Все, зробити Зріз, Зшити
		'''
		X, Y = data[:,0], data[:,1]
		tmpData = []
		tmpPoly = [[], []]
		if AC:
			X, Y, x, y = self.cutConcatView(X, Y)
		
		n = int(N)
		if self.showTmp: tmpData = (X,  Y)
		EQ = sp.poly1d( sp.polyfit(X, Y, m) )
		poly_Y = EQ( X )
		xnew, ynew = [], []
		Range = range(0,len(X),n)
		i = 0
		for j in list(Range[1:])+[len(X)-1]:
			if j-i<=1: break
			x_tmp = X[i:j]
			y_tmp = Y[i:j]
			if discrete:
				polyY_tmp = sp.poly1d( sp.polyfit(x_tmp, y_tmp, m) )(x_tmp)
				tmpPoly[0] += x_tmp.tolist()
				tmpPoly[1] += polyY_tmp.tolist()
			else:	
				polyY_tmp = poly_Y[i:j]
			t = True
			y_old = y_tmp - polyY_tmp
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
			
			for i in window:	x_tmp, y_tmp = x_tmp[i], y_tmp[i]
			xnew = xnew + x_tmp.tolist()
			ynew = ynew + (y_tmp).tolist()
			i = j
		X, Y = sp.array(xnew), sp.array(ynew)
		if AC:
			X, Y = self.cutConcatView(X, Y, x=x, y=y, state=False)
		if self.showTmp:
			if discrete:
				poly = (tmpPoly[0],  tmpPoly[1])
			else: poly = (tmpData[0],  poly_Y)
			return Array(sp.array([X, Y]).T, Type = data.Type,
				scale = data.scale),	tmpData, poly    
		else:	
			return Array(sp.array([X, Y]).T, Type = data.Type,
				scale = data.scale)
	
	
	def averaging(self, data, N=1, m=3,
				discrete=False, step=0.1, AC=False, Approx=False):
		'''	Усереднення між заданими вузлами.
		m	-	порядок полінома
		N	-	кількість вузлів
		step - крок усереднення
		'''
		X, Y = data[:,0], data[:,1]
		#Обрізка в заданих межах
		if AC:
			X, Y, x, y = self.cutConcatView(X, Y)
		if step:
			#n = int(N)
			EQ = sp.poly1d( sp.polyfit(X, Y, m) )
			poly_Y = EQ( X )
			Range = sp.arange(X.min(), X.max(), step)#range(0,len(X),n)
			xnew, ynew = [], []
			poly = [[], []]
			for j in Range:
				#if j-i <=1:	break
				w = ((X>=j) * (X<(j+step)))
				x_t = X[w]
				if len(x_t)>=1 and (j+step<=X.max()):
					#print(len(x_t), "--------------------------------")
					y_t = Y[w]
					x_temp = x_t.mean()
					xnew.append(x_temp)
					if Approx:
					#print(y_t)
						if discrete and len(y_t)>=3:
							eq = sp.poly1d( sp.polyfit(x_t, y_t, m) )
							polyY_tmp = eq(x_t)
							poly[0] += x_t.tolist()
							poly[1] += polyY_tmp.tolist()
						else:
							eq = EQ
							polyY_tmp = poly_Y[w]
						ynew.append( (y_t - polyY_tmp).mean() + eq(x_temp))
					else:
						ynew.append(y_t.mean())
				else: pass  #print("==========")
			if self.showTmp:
				if not discrete:
					poly = (X,  poly_Y)
				
				if AC:
					xnew, ynew = self.cutConcatView(xnew, ynew, x=x, y=y, state=False)
				return Array(sp.array([xnew, ynew]).T, Type = data.Type, scale = data.scale),\
					X, Y, poly
			else:
				if AC:
					xnew, ynew = self.cutConcatView(xnew, ynew, x=x, y=y, state=False)
				return Array(sp.array([xnew, ynew]).T, Type = data.Type, scale = data.scale)
		

	def b_s(self, data, xi=[], Step=1,
			sm=1100000., km = 5, AC=False, Smooth=True):
		'''	Інтерполяція B-сплайном
		sm	-	коефіцієнт згладжування
		km	-	степінь полінома
		'''
		print("B-spline interpolation [s = %.3f, k = %.3f]" % (sm,km))
		X, Y = data[:,0], data[:,1]
		
		#Обрізка в заданих межах
		if AC:
			X, Y, x, y = self.cutConcatView(X, Y)
		if not any(xi):
			
			xi = sp.arange(X.min(), X.max(),Step)
		try:
			if Smooth:
				tckp,u = interp.splprep([X,Y],s=sm,k=km,nest=-1)
				xi, y_interp = interp.splev(sp.linspace(0,1,int((X.max()-X.min())/Step)*10),tckp)
				#y_interp = sp.interpolate.UnivariateSpline(X, Y, s = sm, k = km)(xi)
			else:
				xi, y_interp = bspline.pbs(X, Y, xi, clamp=False)
			if AC:
				xi, y_interp = self.cutConcatView(xi, y_interp, x=x, y=y, state=False)
			if self.showTmp:
				return Array(sp.array([xi, y_interp]).T,Type = data.Type, scale = data.scale),  X,  Y
			else:	return Array(sp.array([xi, y_interp]).T,Type = data.Type, scale = data.scale)
		except:
			pass
			self.mprint("ResEvalError: UnivariateSpline")
			
	####################################################################
	########################  Слоти  ###################################
	####################################################################
	#  page_Filters
	def setFilters(self):
		'''Посадка  на фільтри'''
		Name = self.currentName()
		active = self.getUi([i+'Filt' for i in ['X', 'Y']])
		
		filtBaseNames = list(self.filtersDict.keys())
		print(filtBaseNames)
		M = [1.,1.]
		for i in (0,1):
			Filt = active[i].text().upper().strip().replace(" ","").replace('+',',').split(',')
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
				M[i] = self.resFilters(Filt)
				
		if M[0]!=1. or M[1]!=1.:
			#for i in [0,1]:	self.filtList[Name][i] = M[i]
			data = self.getData(Name)
			if not data is None:
				print(M)
				data[:,0] = data[:,0]/M[0]  #self.filtList[index][0]
				data[:,1] = data[:,1]/M[1]  #self.filtList[index][1]
				self.updateData(array=data)
			#self.mprint("Filters [X,Y]: %s" % str(self.filtList[index]))
	
	
	#  page_ReHi3
	def recalcReHi3(self):
		Name = self.currentName()
		data = self.getData(Name)
		if not data is None:
			AC = self.getUi("processView").isChecked()
			
			a0 = self.ui.reHi3_a0.value()
			Lambda = self.ui.reHi3_lambda.value()
			n0 = self.ui.reHi3_n0.value()
			d = self.ui.reHi3_d.value()
			z = self.ui.reHi3_z.value()
			r0 = self.ui.reHi3_r0.value()
			f = self.ui.reHi3_f.value()
			l = self.ui.reHi3_l.value()
			polyM = self.ui.reHi3_polyM.value()

			dM = self.ui.reHi3_dM.currentText()
			dmDict = {	'cm':	10**-2, 
						'mm':	10**-3,
						'mkm':	10**-6, 
						'nm':	10**-9}
			d *= dmDict[dM]
			#=========================================================================
			'''
			Lambda = 532.
			a0 = 18.
			n0 = 1.5
			d = 8.*10**-2
			f = 8.
			l = 10.
			r0 = 0.1
			z = 79.4
			
			A = 0.07984
			B = 0.01121
			C = -0.00068
			D = 0.
			'''
			
			#=========================================================================
			
			
			a0 *= 25*10**-4
			Lambda *= 10**-7
			
			X = data[:, 0]
			Y = data[:, 1]
			if AC:
				X, Y, x, y = self.cutConcatView(X, Y)
			
			A, B, C, D = 0, 0, 0, 0
			EQ = sp.poly1d( sp.polyfit(X, Y, polyM) )
			A = EQ[0]
			B = EQ[1]
			C = EQ[2]
			
			if polyM == 3:
				D = EQ[3]
			xnew = sp.linspace(X.min(), X.max(), 500)
			ynew = EQ(xnew)
			self.ui.mpl.canvas.ax.plot(xnew,  ynew, '.m',  alpha=0.8,  zorder=1)
			self.ui.mpl.canvas.draw()
			print('EQ: ', A, B, C, D)
			'''
			The first basic calculation (better to join them to calculation formulas)
			'''
			pi, exp, cos, sin, Abs, sqrt = sp.pi, sp.exp, sp.cos, sp.sin, sp.absolute, sp.sqrt
			k = 2.*pi/Lambda
			# difractive distance a0:
			zda0 = (k*(a0)**2.)/2.
			R = ((1.-n0)/(1.+n0))**2.
			# size of the beam on the sample: 
			a = a0*sqrt((1.-l/f)**2+(l/zda0)**2.)
			a1 = (f*(1.-l/f)**2 + (l/zda0)**2)/((1-l/f*(1+(f/zda0)**2)))
			# difractive distance a:
			zda = (k*(a)**2.)/2.
			# coefficients in formula T:
			b = -(k*a**2.)*(1.-z/a1)/(2.*z)
			#also there are needed b**2
			c = a**2*(1.+b**2.)*(z/(zda))**2.
			#the normalizing factor:
			N = 1-exp(-2*(r0)**2/c)                  
			'''
			This is the main part of calculation ( formula for transmittance T includes several summands).
			T decomposition
			'''
			T0 = 1.
			T1 = (-1/(N))*exp(-4*r0**2*(3+b**2)/(c*(9+b**2)))*sin(8*b*(r0)**2/(c*(9+b**2)))
			T2 = (1/(3*N))*(exp(-6*(r0)**2*(5+b**2)/(c*(25.+b**2)))*cos(24*b*(r0)**2/(c*(25+b**2)))-exp(-6*(r0)**2*(1+b**2)/(c*(9+b**2))))
			T3 = (1/(8*N))*(1/3*exp(-8*(r0)**2*(7+b**2)/(c*(49.+b**2)))*sin(48*(r0)**2*b/(c*(49+b**2)))-exp(-8*(r0)**2*(15+b**2)*(1+b**2)/(c*(25+b**2)*(9+b**2)))*sin(16*(r0)**2*b*(1+b**2)/(c*(25+b**2)*(9+b**2))))
			# An additional parameters 
			##D = 0 
			q = 0.1
			s = k*(1-R)*d*(1-exp(-2*q*d)/(2*q))
			# The components of n2                  
			n21 = (T0/T1)*(B/A)*10**(-3)/s
			n22 = sqrt((C/A)*(T0/T2))/s*10**-3
			#n23 = (T0/T3*(D/A))**(1./3.)/s*10**-3
			n23 = (T0/T3*(D/A))**(1./3.+0j)/s*10**-3
			print(type(n23), n23.dtype, n23)
			
			'''
			nonlinear refractive index n2 (n = n0 + n2*I, where I is intensity):
				(there n2 is devided on 2 because we have
					polynomial approximation of the second order)
			'''
			if polyM == 1:
				polyM = 2
			n2 = (Abs(n21)+Abs(n22)+Abs(n23))/(polyM-1)
			# The components of hi3
			hi31 = 3*Abs(n21)*(n0/(4*pi))**2
			hi32 = 3*Abs(n22)*(n0/(4*pi))**2
			hi33 = 3*Abs(n23)*(n0/(4*pi))**2
			
			hi3 = 3*n2*(n0/(4*pi))**2*10**(-3)
			print(1+2j)
			print('S', s, 'N', N, 'k',  k, 'a', 'b', b, 'a', a,
				'zda', zda, 'zda0', 'a1', a1, 'a0', a0, 'c', c, 'R', R,
				'polyM', polyM)
			print('T:', T0, T1, T2, T3)
			print('n', n21, n22, n23, n2)
			print('hi', hi31, hi32, hi33, hi3)
			
			
			#------------------------------------------------------------
			
			if AC:
				X, Y = self.cutConcatView(X, Y, x=x, y=y, state=False)
			
	#  page_NormData
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
			#del self.dataDict[name]
			#print(self.dataDict.keys(), name)
		
		for i in rows[::-1]:
			self.ui.normTable.removeRow(i)
			#self.nameBox.removeItem(i)
		

	def normTableItemClicked(self, item):
		if item.column() == 2:
			name1 = self.ui.normTable.cellWidget(item.row(), 0).currentText()
			name2 = self.ui.normTable.cellWidget(item.row(), 1).currentText()
			name3 = name1 + '_' + name2
			cData = self.getData(name2)
			sData = self.getData(name1)
		
			if cData.scale == [0,0] and sData.scale == [0,0]:
			
			#if self.ui.rButton.isEnabled():
				x = sData[:,0]
				window = (x>=cData[:,0].min())*(x<=cData[:,0].max())
				x = x[window]
				y = sData[:,1]
				y = y[window]
				cY_tmp = sp.interpolate.interp1d(cData[:,0], cData[:,1],self.ui.normEvalType.currentText().lower())(x)
				y = y[cY_tmp != 0]
				cY_tmp = cY_tmp[cY_tmp != 0]
				y = y/ cY_tmp
			else: print('ResEval: interpTypeError')
			self.addToDataTables(Array(sp.array([x,y]).T, Type=2, scale=[0,0], Name=name3))
			self.ui.normTable.item(item.row(), 3).setText(name3)
			self.ui.normTable.item(item.row(), 4).setText('Ok')
	#  page_PolyCut
	def polyCut(self):
		'''Обрізка [за різними методами]'''
		Param = ('N', 'P', 'M')
		Name = self.currentName()
		active = self.findUi(('Poly'+i for i in Param),p="value")
		XY = self.getData(Name)
		if not XY is None:
			discrete = self.getUi('Discrete' ).isChecked()
			AC = self.getUi("processView").isChecked()
			# Межі будемо брати з обраної (графічним методом) ділянки 
			
			data = self.poly_cut(XY, N = active[0], p = active[1],
				m = active[2], AC = AC,  discrete=discrete)
			
			if self.showTmp:
				data,  tmp,  poly = data
			self.updateData(array = Array(data, Type=XY.Type, Name=Name, scale=XY.scale))
			
			if self.showTmp:
				self.ui.mpl.canvas.ax.plot(tmp[0],  tmp[1], '.m',  alpha=0.2,  zorder=1)
				self.ui.mpl.canvas.ax.plot(poly[0],  poly[1],  'r')
				self.ui.mpl.canvas.draw()
				
	#  page_PolyFit
	def polyApprox(self):
		''' Апроксимація поліномом n-го степ. '''
		Name = self.currentName()
		data = self.getData(Name)
		if not data is None:
			X, Y = data[:, 0], data[:, 1]
			step = self.getUi('ApproxStep').value()
			M = self.getUi('ApproxM').value()
			AC = self.getUi("processView").isChecked()
			piece_wise = self.getUi('ApproxPiece_wise').isChecked()
			x, y = X.copy(), Y.copy()
			xnew, ynew = [], []
			EQ = None
			if AC:
				X, Y, x, y = self.cutConcatView(X, Y)
			if piece_wise:
				pass
			else:
				EQ = sp.poly1d( sp.polyfit(X, Y, M) )
				xnew = sp.arange(X.min(), X.max(), step)
				ynew = EQ( xnew )
			
			if AC:
				xnew, ynew = self.cutConcatView(xnew, ynew, x=x, y=y, state=False)
			self.updateData(array = Array(sp.array([xnew, ynew]).T,
				Type=data.Type, scale=data.scale, Name=Name))
			
			if self.showTmp:
				self.ui.mpl.canvas.ax.plot(x,  y, '.m',  alpha=0.2,  zorder=1)
				xl = self.ui.mpl.canvas.ax.get_xlim()
				yl = self.ui.mpl.canvas.ax.get_ylim()
				
				text = ''
				for j, i in enumerate(EQ):
					text+="+"*(i>0) + str(i.round(3))+" x^{" + str(M-j) +"}"
				text = "$" + text[(EQ[0]>0):] + "$"
				print(text)
				
				self.ui.mpl.canvas.ax.text(xl[0], yl[1], text, fontsize=15)
				
				self.ui.mpl.canvas.draw()
			
		
		
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
		Name = self.currentName()
		state = self.getUi('AutoB_splineS').isChecked()
		active = self.getUi(['B_spline' + i for i in spins])
		
		data = self.getData(Name)
		if not data is None:
			active[0].setEnabled(not state)
			
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
					print("AutoB_splineS: SmoothParamError")
			else:
				pass
		
		
	def B_spline(self):
		'''інтерполяція b-сплайном'''
		Name = self.currentName()
		step, sm, km = (i.value() for i in self.getUi(['B_splineStep', 
			'B_splineS', 'B_splineK']))
		XY = self.getData(Name)
		if not XY is None:
			AC = self.getUi("processView").isChecked()
			Smooth = self.getUi('B_splineSmooth').isChecked()
			
			data = self.b_s(XY, Step=step, sm=sm, km=int(km), AC=AC, Smooth=Smooth)
			if self.showTmp:
				data,  x, y = data
				
			self.updateData(array=Array(data, scale=XY.scale, Type=XY.Type, Name=Name))
			
			if self.showTmp:
				self.ui.mpl.canvas.ax.plot(x,  y, '.m',  alpha=0.5,  zorder=1)
				self.ui.mpl.canvas.draw()
				
			
		
	#  page_Average
	def Average(self):
		'''Усереднення за різними методами'''
		Name = self.currentName()
		step = self.getUi('AverageStep').value()
		XY = self.getData(Name)
		if not XY is None:
			M = self.getUi('PolyM').value()
			discrete = self.getUi('Discrete' ).isChecked()
			AC = self.getUi("processView").isChecked()
			##Approx = self.getUi('AverageApprox').isChecked()
			data = self.averaging(XY, step=step,	m=M, discrete=discrete,
						AC=AC, Approx=False )
			if self.showTmp:
				data, x, y, poly = data
			self.updateData(array=Array(data, Type=data.Type, Name=Name, scale=data.scale))
			
			if self.showTmp:
				self.ui.mpl.canvas.ax.plot(x,  y, '.m',  alpha=0.2,  zorder=1)
				##if Approx:
				##	self.ui.mpl.canvas.ax.plot(  poly[0],  poly[1],  'r')
				self.ui.mpl.canvas.draw()
		
		
	#  page_FiltFilt
	def filtFilt(self):
		Name = self.currentName()
		data = self.getData(Name)
		if not data is None:
			p = self.ui.FiltFiltP.value()
			k = self.ui.FiltFiltK.value()
			b, a = butter(k, p)
			data[:, 1] = filtfilt(b, a, data[:, 1])
			data[:, 0] = filtfilt(b, a, data[:, 0])
			self.updateData(data)
			
	
	#  page_data
	def namesBoxLinks(self):
		current = self.nameBox.currentIndex()
		print(current)
		self.ui.namesTable.setCurrentCell(current, 0)
	def saveData(self):
		'''Збереження активного масиву до текстового файлу'''
		if self.sender().objectName() == 'actionSaveData':
			self.ui.stackedWidget.setCurrentWidget(self.getUi('page_Data'))
		Name = self.currentName()
		data = self.getData(Name)
		if not data is None:
			filename = self.fileDialog.getSaveFileName(self,
				'Save File', os.path.join(self.Root, Name))
			if filename:
				sp.savetxt(str(filename), data, delimiter=self.getDelimiter())
				
		
	def tableItemChanged(self, item):
		if not item is None:
			Name = item.text()
			self.mprint(Name)
			if Name in self.dataDict.keys():
				hist = self.dataDict[Name]
				state = False
				if len(hist)>=2:
					state = True
				data = self.getData(item.text())
				self.Plot(data)
				self.dataConfigs[Name]['Reset'] = state
				self.dataConfigs[Name]['Undo'] = state
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

	def deleteFromTable(self):
		#try:
		
		selected = self.ui.namesTable.selectionModel().selectedIndexes()
		rows = []
		for i in selected:
			rows.append(i.row())
			name = self.ui.namesTable.item(i.row(), 0).text()
			del self.dataDict[name]
			print(self.dataDict.keys(), name)
		
		for i in rows[::-1]:
			self.ui.namesTable.removeRow(i)
			self.nameBox.removeItem(i)
			if hasattr(self, 'intensDialog'):
				self.intensDialog.updateActiveDataList()

	def editTableItemName(self, item):

		if item.column() == 0 and self.tableEditedName and not self.nameEditLock\
				and item.text() not in self.dataDict.keys():
			print(self.tableEditedName, item.text(), self.dataDict.keys())
			self.dataDict[item.text()] = self.dataDict[self.tableEditedName]
			del self.dataDict[self.tableEditedName]
			print(self.tableEditedName, item.text(), self.dataDict.keys())
			self.nameEditLock = True
		else:
			if self.tableEditedName:
				self.ui.namesTable.itemChanged.disconnect(self.editTableItemName)
				item.setText(self.tableEditedName)
				self.ui.namesTable.itemChanged.connect(self.editTableItemName)
	def editTableItem(self, clicked):
		if clicked.column() == 0:
			item = self.ui.namesTable.item(clicked.row(), 0)
			self.tableEditedName = item.text()
			self.nameEditLock = False
			
	#=============================================================================
	def setToolsLayer(self):
		name = self.sender().objectName().split('action')[1]
		self.ui.stackedWidget.setCurrentWidget(self.getUi('page_'+name))
		if name == 'B_spline':
			self.AutoB_splineS()
		#elif name == 'Filters':
			
			
	
	
	def movePoint(self):
		'''Переміщення точок'''
		Name = self.currentName()
		data = self.getData(Name)
		if not data is None:
			def on_motion(event):
				if not event.xdata is None and not event.ydata is None:
					xl = self.ui.mpl.canvas.ax.get_xlim() 
					yl = self.ui.mpl.canvas.ax.get_ylim()
					self.ui.mpl.canvas.ax.figure.canvas.restore_region(self.qcut.background)
					self.ui.mpl.canvas.ax.set_xlim(xl)
					self.ui.mpl.canvas.ax.set_ylim(yl)
					nearest_x = sp.absolute(data[:, 0] - event.xdata).argmin()
					#print(nearest_x, data[nearest_x, 1], event.xdata)
					yl = self.ui.mpl.canvas.ax.get_ylim()
					self.qcut.line.set_xdata([event.xdata]*2)
					self.qcut.line.set_ydata(yl)
					self.qcut.points.set_xdata(data[nearest_x, 0])
					self.qcut.points.set_ydata(data[nearest_x, 1])
					# redraw artist
					self.ui.mpl.canvas.ax.draw_artist(self.qcut.line)
					self.ui.mpl.canvas.ax.draw_artist(self.qcut.points)
					self.ui.mpl.canvas.ax.figure.canvas.blit(self.ui.mpl.canvas.ax.bbox)
			
			def on_press(event):
				if not event.xdata is None and not event.ydata is None:
					
					nearest_x = abs(data[:, 0] - event.xdata).argmin()
					#nearest_y = abs(data[:, 1] - event.ydata).argmin()
					
					data[nearest_x, 1] = event.ydata
					self.updateData(array=data)
					
					xl = self.ui.mpl.canvas.ax.get_xlim()
					self.ui.mpl.canvas.ax.plot(xl, [1]*2, '-.r')
					self.ui.mpl.canvas.ax.plot(event.xdata, 1, 'ro', markersize=6)
					self.ui.mpl.canvas.draw()
					self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
					self.ui.mpl.canvas.mpl_disconnect(self.cidmotion)
				else:
					self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
					self.ui.mpl.canvas.mpl_disconnect(self.cidmotion)
				
			self.cidmotion = self.ui.mpl.canvas.mpl_connect(
					  'motion_notify_event', on_motion)
			self.cidpress = self.ui.mpl.canvas.mpl_connect(
						'button_press_event', on_press)
		
	
	
	def showProj(self, clicked):
		self.projects[clicked.text()].activateWindow()
		self.projects[clicked.text()].raise_()
		self.projects[clicked.text()].show()
	def addToProj(self):
		'''Додати дані до проекту'''
		name = self.sender().objectName()
		print(self.projects.keys(),"name:",  name)
		proj = self.projects[name[4:]]
		Type = self.currentType()
		proj.addToList(self.getData(Type))
		
	def createProj(self):
		'''Створити проект'''
		#setName = NameDialog(self)
		#setName.exec_()
		name = "newProj"#setName.name
		while name in self.projects.keys():
			if name[-1].isdigit():
				name = name[:-1] + str(int(name[-1])+1)
			else: name += '0'

		project = ProjectDialog(self, name=name)
		
		
		#if not name:
		name = 'new'
		Type = self.currentType()
		if Type >= 0:
			project.addToList(self.getData(Type), name=name)
			project.show()
		item = QtGui.QListWidgetItem()
		item.setText(project.projName)
		self.ui.projList.addItem(item)
		self.projects.update({project.projName : project})
		print(self.projects)
		
		
	def rYInPercents(self, state):
		''' Певеведення у відсотки Y результату '''
		data = self.getData(2)
		if state:
			data[:, 1] *= 100.
		else:
			data[:, 1] /= 100.
		self.updateData(array=data)
	
	## norm
	def norm_FirstPoint(self):
		''' Нормування на першу точку '''

		Name = self.currentName()
		data = self.getData(Name)
		if not data is None:
			try:
				data[:, 1] /= data[0, 1]
				self.updateData(array=data)
				xl = self.ui.mpl.canvas.ax.get_xlim()
				self.ui.mpl.canvas.ax.plot(xl, [1]*2, 'r')
				self.ui.mpl.canvas.ax.plot(data[0, 0], 1, 'ro', markersize=6)
				self.ui.mpl.canvas.draw()
			except:
				pass
				
	def norm_Max(self):
		''' Нормування на максимум '''
		Name = self.currentName()
		data = self.getData(Name)
		if not data is None:
			try:
				data[:, 1] /= data[:, 1].max()
				self.updateData(array=data)
			except:
				pass
				
	def norm_Point(self):
		''' Нормувати на вказану точку '''

		def on_press(event):
			''' Отримання координат точки для нормування на точку '''
			if not event.xdata is None and not event.ydata is None:
				Name = self.currentName()
				data = self.getData(Name)
				if not data is None:
					data[:, 1] /= event.ydata
					self.updateData(array=data)
					xl = self.ui.mpl.canvas.ax.get_xlim()
					self.ui.mpl.canvas.ax.plot(xl, [1]*2, 'r')
					self.ui.mpl.canvas.ax.plot(event.xdata, 1, 'ro', markersize=6)
					self.ui.mpl.canvas.draw()
					self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
					self.ui.mpl.canvas.mpl_disconnect(self.cidmotion)
					
		def on_motion(event):
			if not event.xdata is None and not event.ydata is None:
				xl = self.ui.mpl.canvas.ax.get_xlim() 
				yl = self.ui.mpl.canvas.ax.get_ylim()
				self.ui.mpl.canvas.ax.figure.canvas.restore_region(self.qcut.background)
				self.ui.mpl.canvas.ax.set_xlim(xl)
				self.ui.mpl.canvas.ax.set_ylim(yl)
				

				self.qcut.line.set_xdata(xl)
				self.qcut.line.set_ydata([event.ydata]*2)
	
				# redraw artist
				self.ui.mpl.canvas.ax.draw_artist(self.qcut.line)
				self.ui.mpl.canvas.ax.figure.canvas.blit(self.ui.mpl.canvas.ax.bbox)
				
		self.cidpress = self.ui.mpl.canvas.mpl_connect(
					'button_press_event', on_press)
		self.cidmotion = self.ui.mpl.canvas.mpl_connect(
				  'motion_notify_event', on_motion)
	
	def plotTmp(self, state):
		'''Проміжні побудови'''
		self.showTmp = state
		if not state: self.qcut.update_graph()
		
	def setLength(self, length):
		'''Вибір довжини хвилі зі списку'''
		self.LENGTH = length.encode('utf_8')
		self.intensDialog.ui.length.setValue(float(self.LENGTH))
		# Оновлення таблиці фільтрів
		self.filtersDict = self.getFilters(length = self.LENGTH)
		self.barWaveLen.setText(length)
		'''
		if self.ui.typeExp.currentIndex() == 1:
			self.K = self.kPICODict[self.LENGTH]
			self.ui.calibr.setText(str(self.K))
		else: pass
		'''
	def applyFilt(self):
		'''Застосування фільтрів із бази для відповідних XY'''
		key = self.sender().objectName()[0]
		index = self.Types[key]
		active = self.findUi([key + i + 'Filt' for i in ('X','Y')])
		self.filtersDict = self.getFilters(length = self.LENGTH)
		filtBaseNames = list(self.filtersDict.keys())
		print(filtBaseNames)
		M = [1.,1.]
		for i in (0,1):
			Filt = active[i].text().upper().strip().replace(" ","").replace('+',',').split(',')
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
				M[i] = self.resFilters(Filt)
				
		if M[0]!=1. or M[1]!=1.:
			for i in [0,1]:	self.filtList[index][i] = M[i]
			data = self.getData(index)
			data[:,0] = data[:,0]/self.filtList[index][0]
			data[:,1] = data[:,1]/self.filtList[index][1]
			self.updateData(array = data)
			#self.mprint("Filters [X,Y]: %s" % str(self.filtList[index]))
	
	
	# Повернути масштаб при поверненні в історії
	def setPrevScale(self, Name=None, action=0):
		##Names = ( 'Y_XScale', 'XLogScale', 'YLogScale', 'LogScale' )
		#__________________________
		actions = ('actionY_X', 'actionX_Log10', 'actionY_Log10' )
		##Types = ('c', 's', 'r')
		Name = self.currentName()
		
		if action == 0 or action == -1:
			data = self.getData(Name)
			if not data is None:
				scale = data.Scale()
				##ui_obj = self.findUi(( Types[Type] + i for i in Names))
				#__________________________
				ui_actions = self.getUi(actions)
				
				##for t in ui_obj[:-1]:
				##	t.toggled[bool].disconnect(self.setNewScale)
				#__________________________

				for t in ui_actions:
					t.toggled[bool].disconnect(self.setNewScale)
					t.setEnabled(False)
					t.setChecked(False)
				if scale[1] == 2:
					##ui_obj[0].setChecked(True)
					#__________________________
					ui_actions[0].setChecked(True)
				else:
					##ui_obj[0].setChecked(False)
					##ui_obj[1].setChecked(scale[0])
					##ui_obj[2].setChecked(scale[1])
					#__________________________
					for i, j in enumerate((False, scale[0], scale[1])):
						ui_actions[i].setChecked(j)
				##ui_obj[0].setEnabled( not (ui_obj[1].isChecked() or ui_obj[2].isChecked()))
				##ui_obj[3].setEnabled( not ui_obj[0].isChecked() )
				#__________________________
				ui_actions[0].setEnabled( not (ui_actions[1].isChecked() or ui_actions[2].isChecked()))
				ui_actions[1].setEnabled( not ui_actions[0].isChecked() )
				ui_actions[2].setEnabled( not ui_actions[0].isChecked() )
				
				self.dataConfigs[Name]['Scale'] = scale
				##for t in ui_obj[:-1]:
				##	t.toggled[bool].connect(self.setNewScale)
				#__________________________
				
				for t in ui_actions:
					t.toggled[bool].connect(self.setNewScale)
				
		else: pass
		
	# Змінити масштаб на новий
	def setNewScale(self, state):
		##Names = ( 'Y_XScale', 'XLogScale', 'YLogScale', 'LogScale')
		actions = ('actionY_X', 'actionX_Log10', 'actionY_Log10' )
		senderName = self.sender().objectName()
		Name = self.currentName()
			
		##t, Type = senderName[0], self.Types[senderName[0]]
		data = self.getData(Name)
		if not data is None:
			Scale = data.Scale()
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
				##ui_obj[3].setEnabled(not ui_obj[0].isChecked())
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
					##ui_obj[0].setEnabled(
					##	not (ui_obj[1].isChecked() or ui_obj[2].isChecked()))
					ui_actions[0].setEnabled(
						not (ui_actions[1].isChecked() or ui_actions[2].isChecked()) )
			self.dataConfigs[Name]['Scale'] = Scale
			data.scale = Scale
			self.updateData(array=Array(data, Name=Name, scale=Scale))

	def ResEval(self):
		""" Обчислюємо результат."""

		cData = self.getData(0)
		sData = self.getData(1)
		
		if cData.scale == [0,0] and sData.scale == [0,0]:
			
			if self.ui.rButton.isEnabled():
				x = sData[:,0]
				window = (x>=cData[:,0].min())*(x<=cData[:,0].max())
				x = x[window]
				y = sData[:,1]
				y = y[window]
				cY_tmp = sp.interpolate.interp1d(cData[:,0], cData[:,1],self.ui.rEvalType.currentText().lower())(x)
				y = y[cY_tmp != 0]
				cY_tmp = cY_tmp[cY_tmp != 0]
				y = y/ cY_tmp
			else: print('ResEval: interpTypeError')
			
			self.updateData(array = Array(sp.array([x,y]).T, Type = 2, scale = [0,0]),action = 0)
		else: print('ResEval: scaleError')
			
	
	"""
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
		Y_new = y + poly_Y
		self.updateData(array = Array(sp.array([X, Y_new]).T, Type = XY.Type, scale = XY.scale))
		
		if self.showTmp:
			self.ui.mpl.canvas.ax.plot(X,  Y, '.m',  alpha=0.2,  zorder=1)
			self.ui.mpl.canvas.ax.plot(  X,  poly_Y,  'r')
			self.ui.mpl.canvas.draw()
	"""	
		
	def Undo(self):
		'''Відкат до попередніх даних'''
		Name = self.currentName()
		if len(self.dataDict[Name])>=2:
			self.updateData(Name=Name, action=-1)
		else:
			self.dataConfigs[Name]['Undo'] = False
			self.sender().setEnabled(False)

	def Reset(self):
		'''Скидання історії'''
		Name = self.currentName()
		if len(self.dataDict[Name])>=2:
			self.updateData(Name=Name, action=0)
		else:
			self.dataConfigs[Name]['Reset']=False
			self.sender().setEnabled(False)

	def confCurrent(self, index):
		'''Побудова й налаштування поточної вкладки'''
		if index > 0:
			Type = index-1
			print('configs', self.dataConfigs)
			# setEnabled
			for i in ('Reset', 'Undo'):
				self.getUi(i).setEnabled(self.dataConfigs[Type][i])
			# setEnabled - Scale
			scale = self.dataConfigs[Type]['Scale']
			ui_scale = self.getUi(
				('actionY_X', 'actionX_Log10', 'actionY_Log10' ))
			for t in ui_scale:
				t.toggled[bool].disconnect(self.setNewScale)
				# Вимикаємо все
				t.setChecked(False)
				t.setEnabled(False)
			if scale[1] == 2:
				ui_scale[0].setEnabled(True)
				ui_scale[0].setChecked(True)
			else:
				ui_scale[0].setEnabled(not any(scale))
				for j, i in enumerate(ui_scale[1:]):
					i.setEnabled(True)
					i.setChecked(bool(scale[j]))
					
			for t in ui_scale:
				t.toggled[bool].connect(self.setNewScale)
			
			
			if sp.any(self.getData(Type)):
				active = self.getData(Type);
				self.Plot(active)
				
			else: pass
			for i in ('menu_Hist', 'menu_Scale'):
				self.getUi(i).setEnabled(True)
		else:
			# setEnabled
			for i in ('menu_Hist', 'menu_Scale'):
				self.getUi(i).setEnabled(False)
			for i in ('actionY_X', 'actionX_Log10', 'actionY_Log10'):
				ui = self.getUi(i)
				ui.toggled[bool].disconnect(self.setNewScale)
				ui.setChecked(False)
				ui.toggled[bool].connect(self.setNewScale)
		
	def getBackFromQcut(self):
		''' Отримання даних, що змінені вручну в QCut'''
		try:
			print( "QCut -> "+str(sp.shape(self.qcut.tdata)),
				self.qcut.tdata.Type, self.qcut.tdata.scale)
			data, Type, Scale = self.qcut.getData()
			Name = self.currentName()
			self.updateData( array = Array(data, Type = Type, scale=Scale, Name=Name)  )
		except:
			pass
		
	def pathTextChanged(self, text):
		"""Якщо поле з шляхом до файлу для завантаження було змінене"""
		state = os.path.exists(self.ui.filePath.text())

		if not state:
			self.sender().setStyleSheet('background-color: magenta;')
		else:
			self.sender().setStyleSheet('background-color: inherited;')
		self.ui.addToTable.setEnabled(state)
		
	def getFilePath(self):
		'''Вибір файлу для завантаження'''
		path = str(self.fileDialog.getOpenFileName(self,'Open File', self.Root))
		if path:
			self.Root = os.path.dirname(path)
			#self.Path[active[0]] = path
			self.ui.filePath.setText(path)
		self.ui.addToTable.setEnabled(os.path.exists(self.ui.filePath.text()))
			
	
	
	def addData(self):
		'''Завантаження даних з файлів'''
		
		path = self.ui.filePath.text()
		print(path)
		if os.path.exists(path):
			#try:
				
				data = sp.loadtxt(path, delimiter=self.getDelimiter())

				attr = self.findUi([i + 'Column' for i in ('x', 'y', 'm')])
				xc = attr[0].value()
				yc = attr[1].value()
				mc = attr[2].value()
				if self.ui.isNormColumn.isChecked():
					XY = sp.array( [data[:,xc], data[:,yc] ]).T / sp.array([data[:,mc], data[:,mc]]).T
				else:
					XY = sp.array( [data[:,xc], data[:,yc] ]).T
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
				
				
				Name = os.path.splitext(os.path.basename(path))[0]
				while Name in self.dataDict.keys():
					if Name[-1].isdigit() and Name[-2] == '_':
						Name = Name[:-1] + str(int(Name[-1])+1)
					else: Name += '_0'
					
				state = 1 #---------------------------------------------
				print(self.dataConfigs.keys())
				if state:
					self.addToDataTables(Array(XY, scale=[0, 0], Type=0, Name=Name), xc=xc, yc=yc)
			#except (ValueError, IOError, IndexError):
			#	self.mprint("loadData: readError")
		else:  self.mprint('loadData: pathError')
			
	
	
	def dataListener(self,Name, action):
		"""Обробка зміни даних"""
		active = self.getData(Name)
		if not active is None:
			self.mprint("dataChanged: scaleX : %d, scaleY : %d, type : %d, name : %s, len : %d, action : %d" %\
				  (active.scaleX, active.scaleY ,active.Type, active.Name, sp.shape(active)[0],action))
			print(self.dataDict.keys())
			if sp.any(active):
				
				self.AutoB_splineS()
				##### Undo/Reset
				hist = self.dataDict[Name]
				state = False
				if len(hist)>=2:
					state = True
				self.dataConfigs[Name]['Reset'] = state
				self.dataConfigs[Name]['Undo'] = state
				self.ui.Reset.setEnabled(state)
				self.ui.Undo.setEnabled(state)
				
	def closeEvent(self, event):
		#self.qcut.close()
		if hasattr(self, 'intensDialog' ):
			self.intensDialog.close()
	
	#======================= intens  =============================
		
	def recalcIntens(self):
		self.intensDialog.typeExp(self.settings.ui.typeexp.currentIndex())
		self.intensDialog.show()
		print(self.intensDialog.Ai2)
		
	####################################################################
	########################  Допоміжні методи  ########################
	####################################################################
	def addToDataTables(self, array, xc='-', yc='-'):
		Name = array.Name 
		self.dataConfigs[Name] = self.confDict.copy()
		counter = self.ui.namesTable.rowCount()
		counter += 1
		self.ui.namesTable.setRowCount(counter)
		self.ui.namesTable.setColumnCount(3)
		self.ui.namesTable.itemChanged.disconnect(self.editTableItemName)
		newItem0 = QtGui.QTableWidgetItem()
		newItem0.setText(Name)
		self.ui.namesTable.setItem(counter - 1, 0, newItem0)
		newItem1 = QtGui.QTableWidgetItem()
		newItem1.setText(str(xc))
		newItem1.setFlags(QtCore.Qt.ItemIsEnabled)
		self.ui.namesTable.setItem(counter - 1, 1, newItem1)
		
		newItem2 = QtGui.QTableWidgetItem()
		newItem2.setText(str(yc))
		newItem2.setFlags(QtCore.Qt.ItemIsEnabled)
		self.ui.namesTable.setItem(counter - 1, 2, newItem2)
		

		self.ui.namesTable.itemChanged.connect(self.editTableItemName)
		
		self.ui.namesTable.clearSelection()
		self.ui.namesTable.setCurrentCell(counter - 1,0)
		self.updateData(array = array, action=0)
		self.nameBox.currentIndexChanged.disconnect(self.namesBoxLinks)
		self.nameBox.clear()
		for i in range(counter):
			text = self.ui.namesTable.item(i, 0).text()
			self.nameBox.addItem(text)
		current = self.ui.namesTable.currentRow()
		print(current)
		self.nameBox.currentIndexChanged.connect(self.namesBoxLinks)
		self.nameBox.setCurrentIndex(current)
		if hasattr(self, 'intensDialog'):
				self.intensDialog.updateActiveDataList()
	def getNamesList(self):
		'''Доступ до списку імен даних'''
		counter = self.ui.namesTable.rowCount()
		names = []
		for i in range(counter):
			names.append(self.ui.namesTable.item(i, 0).text())
		return names
		
	def getDelimiter(self):
		'''Вибір розділювачів даних'''
		delimiters = {
			'space': ' ',
			'space space': '  ', 
			'tab': '\t', 
			',': ',', 
			'.': '.', 
			';': ';'
			}
		return delimiters[self.ui.delimiter.currentText()]
		
	def currentName(self):
		row = self.ui.namesTable.currentRow()
		if self.ui.namesTable.item(row, 0) is None:
			print('Name: None')
			return
		else:
			return self.ui.namesTable.item(row, 0).text()
		

	def getUi(self, attrNames):
		if type(attrNames) in (type([]), type(())):
			return tuple(getattr(self.ui, i) for i in attrNames)
		else:
			return getattr(self.ui, attrNames)
		
	def formatedUpdate(self, data, scale, Type, Name):
		self.updateData(Array(data, scale=scale, Type=Type, Name=Name))

	def mprint(self, m):
		'''Вивід повідомлень в поле статусу'''
		self.ui.statusbar.showMessage(m)
		print(m)
	
	def Plot(self, array):
		self.OPT['defaulTabType'] = array.Type
		self.qcut.Plot(array)
		
	def updateData(self, array = Array(sp.zeros((0,2)),scale=[0,0], Type=0, Name='new'),
				action=1, Type=None, Name=None):
		""" Запис в тимчасовий файл даних з масиву
		action = {-1, 0, 1, 2}
			-1	:	undo
			0	:	reset
			1	:	add
		"""
		if not array is None:
			if Type is None:
				if sp.any(array):
					Type = array.Type
			
			if Name is None:
				if sp.any(array):
					Name = array.Name
			emit = False
			if Name not in self.dataDict.keys():
				self.dataDict[Name] = [array]
			arrayLen = len(self.dataDict[Name])
			# Запис в історію
			if action == 1:
				if sp.any(array) and sp.shape(array)[1] == 2\
						and sp.shape(array)[0] > 1:
					self.dataDict[Name].append(array)
					emit = True

				else: print('updateData: arrayError',sp.any(array) ,
							sp.shape(array)[1] == 2 , sp.shape(array)[0] > 1)
			
			# Видалення останнього запису
			elif action == -1 and arrayLen>=2:
				self.dataDict[Name].pop()
				emit = True
				
			# Скидання історії, або запис першого елемента історії
			elif action == 0:
				print(0)
				if sp.any(array) and sp.shape(array)[1] == 2\
						and sp.shape(array)[0] > 1 and arrayLen>=1:
					self.dataDict[Name] = []
					self.dataDict[Name].append(array)
					emit = True
				if not sp.any(array) and arrayLen>=2:
					self.dataDict[Name][1:] = []
					emit = True
				
			else:
				print("updateData: Error0",len(self.dataDict[Name]))
				print(sp.shape(self.getData(Name)))
			
			# Емітувати повідомлення про зміу даних
			if emit:
				self.data_signal.emit(Name, action)
				self.Plot(self.getData(Name) )
			return emit
	def getData(self,Name):
		#if type(Name) == type(''):
		#	Type = self.Types[Type]
		if Name is None:
			print('Data: None')
			return
		else:
			return self.dataDict[Name][-1].copy()
	
	def getFilters(self, length="532"):
		"""Читання таблиці фільтрів та вибір значень для даної довжини хвилі"""
		filt = sp.loadtxt(self.FiltersPath, dtype="S")
		col = sp.where(filt[0,:]==length)[0][0]
		output = dict( zip(filt[1:,0], sp.array(filt[1:,col],dtype="f") ) )
		self.ui.filtersList.clear()
		for i in output.keys():
			self.ui.filtersList.addItem(str(i, 'utf-8'))
		return output
	def resFilters(self,filters):
		"""Перерахунок для різних комбінацій фільтрів"""
		return  sp.multiply.reduce( 
				[ self.filtersDict[i.encode('utf-8')] for i in filters] )
	
	
	# Пошук однотипних об’єктів графічної форми за кортежем імен
	def findChilds(self,obj,names, p = ''):
		'''Додатковий механізм пошуку об’єктів графічної форми
		p	-	атрибут який повертається для кожного елемента
		'''
		if p == 'value':
			return tuple(self.findChild(obj,name).value() for name in names)
		elif p == 'checkState':
			return tuple(self.findChild(obj,name).checkState() for name in names)
		else: return tuple(self.findChild(obj,name) for name in names)
	def findUi(self, names, p = ''):
		if p == 'value': return [ getattr(self.ui, i).value() for i in names ]
		else: return [ getattr(self.ui, i) for i in names ]
	
	def uiConnect(self):
		'''Пов’язвння сигналів з слотами'''
		
		##############  Filters    ###############################################
		self.ui.FiltOk.clicked.connect(self.setFilters)
		##############  ReHi3      ###############################################
		self.ui.reHi3_ok.clicked.connect(self.recalcReHi3)
		##############  NormData   ###############################################
		self.ui.normDataAdd.clicked.connect(self.normDataAdd)
		self.ui.normDataRemove.clicked.connect(self.normDataRemove)
		self.ui.normTable.itemClicked.connect(self.normTableItemClicked)
		
		##############  PolyFit    ###############################################
		self.ui.PolyApprox.clicked.connect(self.polyApprox)
		##############  PolyCut    ###############################################
		self.ui.PolyOk.clicked.connect(self.polyCut)
		
		##############  B_spline   ###############################################
		self.ui.B_splineOk.clicked.connect(self.B_spline)
		self.ui.AutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		self.ui.AutoB_splineS.toggled[bool].connect(self.connectAutoB_sS)
		##############  Average    ###############################################
		self.ui.AverageOk.clicked.connect(self.Average)
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
		self.data_signal[str,int].connect(self.dataListener)
		self.data_signal[str,int].connect(self.setPrevScale)
		##########################################################################
		

		
		self.ui.Undo.triggered.connect(self.Undo)
		self.ui.Reset.triggered.connect(self.Reset)
		
		#self.ui.cPolyOk.clicked.connect(self.polyCut)
		#self.ui.sPolyOk.clicked.connect(self.polyCut)
		#self.ui.cAverageOk.clicked.connect(self.Average)
		#self.ui.sAverageOk.clicked.connect(self.Average)
		#self.ui.cPolyApprox.clicked.connect(self.PolyApprox)
		#self.ui.sPolyApprox.clicked.connect(self.PolyApprox)
		#self.ui.rPolyApprox.clicked.connect(self.PolyApprox)
		
		#self.ui.cMedFilt.clicked.connect(self.medFilt)
		#self.ui.sMedFilt.clicked.connect(self.medFilt)
		#self.ui.rMedFilt.clicked.connect(self.medFilt)
		
		#self.ui.cB_splineOk.clicked.connect(self.B_spline)
		#self.ui.sB_splineOk.clicked.connect(self.B_spline)
		#self.ui.rB_splineOk.clicked.connect(self.B_spline)
		#self.ui.rButton.clicked.connect(self.ResEval)
		#self.ui.cAutoInterval.toggled[bool].connect(self.AutoInterval)
		#self.ui.sAutoInterval.toggled[bool].connect(self.AutoInterval)
		#self.ui.rAutoInterval.toggled[bool].connect(self.AutoInterval)
		#self.ui.cAutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		#self.ui.cAutoB_splineS.toggled[bool].connect(self.connectAutoB_sS)
		#self.ui.sAutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		#self.ui.sAutoB_splineS.toggled[bool].connect(self.connectAutoB_sS)
		#self.ui.rAutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		#self.ui.rAutoB_splineS.toggled[bool].connect(self.connectAutoB_sS)
		
		#self.ui.cSave.clicked.connect(self.Save)
		#self.ui.sSave.clicked.connect(self.Save)
		#self.ui.rSave.clicked.connect(self.Save)
		#self.ui.tmpShow.toggled[bool].connect(self.plotTmp)
		#self.ui.createProj.triggered.connect(self.createProj)
		
	
		## norm
		self.ui.norm_Max.triggered.connect(self.norm_Max)
		self.ui.norm_Point.triggered.connect(self.norm_Point)
		self.ui.norm_FirstPoint.triggered.connect(self.norm_FirstPoint)
		
		
		self.ui.settings.triggered.connect(self.settings.show)
		# Масштабування
		self.ui.actionY_X.toggled[bool].connect(self.setNewScale)
		##self.ui.checkY_X.toggled[bool].connect(self.ui.actionY_X.toggle)
		self.ui.actionY_Log10.toggled[bool].connect(self.setNewScale)
		self.ui.actionX_Log10.toggled[bool].connect(self.setNewScale)
		#self.ui.rYInPercents.toggled[bool].connect(self.rYInPercents)
		self.ui.movePoint.triggered.connect(self.movePoint)
		self.ui.Close.triggered.connect(self.close)
		#self.close.connect(self.closeEvent)
		#self.ui.LENGTH.currentIndexChanged[str].connect(self.setLength)
		#___________________________		_____________________
		
		
		#+++++++++++++++++++  Intensity     ++++++++++++++++++++++++++++++++++++++
		self.ui.recalcIntens.triggered[bool].connect(self.recalcIntens)
		#self.ui.typeExp.currentIndexChanged[int].connect(self.typeExp)
		#self.ui.calibr.editingFinished.connect(self.calibrChanged)
		####################  intensDialog  ######################################
		#self.ui.recalcForIntens.clicked.connect(self.recalcForIntens)
		#self.intensDialog.ui.buttonBox.accepted.connect(self.getIntens)
		
		
		#self.ui.tabWidget.doubleClicked.connect(self.toggleTabs)
		#self.ui.toggleTabs.toggled.connect(self.toggleTabs)
		self.ui.projList.itemDoubleClicked.connect(self.showProj)
		self.ui.console.triggered.connect(self.console.show)
		
		####################  calibrDialog  ######################################
		#self.calibrDialog.ui.ok.clicked.connect(self.getCalibr)
		#self.ui.recalcCalibr.clicked.connect(self.recalcCalibr)
		####################  mainToggle    ######################################
		self.ui.actionPolyCut.triggered.connect(self.setToolsLayer)
		self.ui.actionPolyFit.triggered.connect(self.setToolsLayer)
		self.ui.actionB_spline.triggered.connect(self.setToolsLayer)
		self.ui.actionAverage.triggered.connect(self.setToolsLayer)
		self.ui.actionFiltFilt.triggered.connect(self.setToolsLayer)
		self.ui.actionData.triggered.connect(self.setToolsLayer)
		self.ui.actionNormData.triggered.connect(self.setToolsLayer)
		self.ui.actionReHi3.triggered.connect(self.setToolsLayer)
		self.ui.actionFilters.triggered.connect(self.setToolsLayer)
		
		#self.ui.actionProjects.triggered.connect(self.setToolsLayer)
		#self.ui.actionPlot.triggered.connect(self.setToolsLayer)
		#self.ui.actionPolyCut.triggered.connect(self.setToolsLayer)
		
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!tab widget with hiding!!!!!!!!!!!!!!!!
	def setTool(self,objType, objName): return self.findChild(objType,objName)
	
if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal.SIG_DFL) # Застосування Ctrl+C в терміналі
	app = QtGui.QApplication(sys.argv)
	win = QTR()
	win.show()
	
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	win.setTool(QtGui.QLineEdit,'filePath').setText("/home/kronosua/work/QTR/data/Cr2.dat")
	#win.setTool(QtGui.QLineEdit,'sPath').setText("/home/kronosua/work/QTR/data/LCg1pl30.dat")
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	
	sys.exit(app.exec_())
	
