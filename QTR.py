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

#from setName import NameDialog

#from calibr import CalibrDialog
# Масив даних, що буде містити дані, їх масштаб та тип
class Array(sp.ndarray):
	
	def __new__(cls, input_array, scale=[0,0], Type = None):
		# Input array is an already formed ndarray instan ce
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
	projects = {}
	Path = ['','','']				# Шляхи до файлів
	Root = os.getcwd()				# Поточний каталог
	FiltersPath = os.path.join(os.getcwd(),"filters.csv")	# База фільтрів
	Types = {'c': 0, 's': 1, 'r': 2}
	
	
	filtersDict = {}				# Словник фільтрів
	filtList = ([1.,1.], [1.,1.])	# Поточні фільтри
	LENGTH = b"1064"				# Довжина хвилі за замовчуванням
	# Стек історії для кроса. зразка і результата
	dataStack = (
		[Array(sp.zeros((0,2)), Type = 0, scale=[0,0])],
		[Array(sp.zeros((0,2)), Type = 1, scale=[0,0])],
		[Array(sp.zeros((0,2)), Type = 2, scale=[0,0])] )
	
	showTmp = False		# Показувати проміжні  побудови
	
	confDict = dict(
		Scale=[0, 0], 
		Reset=False,
		Undo=False
		)
	dataConfigs = (confDict.copy(), confDict.copy(), confDict.copy())
	
	OPT = {	'proc' : False, 
			'defaultTabType' : 0, 
			'projN' : 0
			}
	
	# DataUpdated signal -> slot
	# Сигнал про зміну в даних
	data_signal = QtCore.pyqtSignal(int, int, name = "dataChanged")
	
	def __init__(self, parent=None):
		super(QTR, self).__init__(parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
		
		self.fileDialog = QtGui.QFileDialog(self)
		
		self.qcut = DesignerMainWindow(parent=self)
		#self.qcut.show()
		# Відкат даних із QCut
		self.qcut.dataChanged.connect(self.getBackFromQcut)
		#self.qcut.show()
		self.intensDialog = IntensDialog(parent=self)
		
		
		
		self.ui.tab_2.setEnabled(False)
		self.ui.tab_3.setEnabled(False)
		self.ui.tab_4.setEnabled(False)
		
		self.settings = SettingsDialog(parent=self)
		#QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, self.close)
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
	def movePoint(self):
		'''Переміщення точок'''
		Type = self.currentType()
		data = self.getData(Type)
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
	
	def toggleTabs(self, state):
		'''Приховування вкладок'''
		self.sender().setText([">", "<"][state])
		self.ui.tabWidget.setVisible(state)
	
	
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
	
	def norm_FirstPoint(self):
		''' Нормування на першу точку '''
		Type = self.currentType()
		if Type != -1:
			data = self.getData(Type)
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
		Type = self.currentType()
		if Type != -1:
			data = self.getData(Type)
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
				Type = self.currentType()
				data = self.getData(Type)
				data[:, 1] /= event.ydata
				self.updateData(array=data)
				xl = self.ui.mpl.canvas.ax.get_xlim()
				self.ui.mpl.canvas.ax.plot(xl, [1]*2, 'r')
				self.ui.mpl.canvas.ax.plot(event.xdata, 1, 'ro', markersize=6)
				self.ui.mpl.canvas.draw()
				self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
		
		self.cidpress = self.ui.mpl.canvas.mpl_connect(
					'button_press_event', on_press)
		
	def plotTmp(self, state):
		'''Проміжні побудови'''
		self.showTmp = state
		if not state: self.qcut.update_graph()
		
	def setLength(self, length):
		'''Вибір довжини хвилі зі списку'''
		self.LENGTH = length.encode('utf_8')
		self.intensDialog.ui.length.setValue(float(self.LENGTH))
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
	def setPrevScale(self, Type, action):
		##Names = ( 'Y_XScale', 'XLogScale', 'YLogScale', 'LogScale' )
		#__________________________
		actions = ('actionY_X', 'actionX_Log10', 'actionY_Log10' )
		##Types = ('c', 's', 'r')
		Type = self.currentType()
		if Type>=0:	
			if action == 0 or action == -1:
				data = self.getData(Type)
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
				
				self.dataConfigs[Type]['Scale'] = scale
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
		Type = self.currentType()
		if Type>=0:	
			##t, Type = senderName[0], self.Types[senderName[0]]
			data = self.getData(Type)
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
			self.dataConfigs[Type]['Scale'] = Scale
			self.updateData(array = Array(data, Type = Type, scale = Scale))

	def Save(self):
		'''Збереження активного масиву до текстового файлу'''
		#Dict = {'cSave' : 0, 'sSave' : 1, 'rSave' : 2}
		senderName = self.sender().objectName()
		active = self.Types[senderName[0]]  #Dict[senderName]
		data = self.getData(active)
		prefix, suffix = '', ''
		if self.ui.rSaveSuffix.text():
			suffix = "_" + self.ui.rSaveSuffix.text()
		if self.ui.rSavePrefix.text():
			prefix = self.ui.rSavePrefix.text() + "_"
			
		newName = prefix + os.path.split(self.Path[1])[1].split('.')[0] + '_' +\
							os.path.split(self.Path[0])[1].split('.')[0] + suffix + '.dat'
							
		filename = self.fileDialog.getSaveFileName(self,
			'Save File', os.path.join(self.Root,  newName))
		if filename:
			sp.savetxt(str(filename), data, delimiter=self.settings.getDelimiter())
			
	def connectAutoB_sS(self, state):
		key = self.sender().objectName()[0]
		spins = ['S', 'Step', 'K']
		for j in spins:
			if state:
				self.getUi(key + 'B_spline' + j).valueChanged.connect(
								self.AutoB_splineS)
			else:
				self.getUi(key + 'B_spline' + j).valueChanged.disconnect(
								self.AutoB_splineS)
								
	def AutoB_splineS(self, state=None, Type=None, param=0.98):
		'''Штучний підбір коефіцієнтів для b-сплайн інтерполяції'''
		spins = ('S',  'Step', 'K')
		keys = ['c', 's', 'r']
		print(state, Type, self.sender().objectName())
		if not state is None:
			Type = self.Types[self.sender().objectName()[0]]
		key = keys[Type]
		
		if not Type is None:
			state = self.getUi(key + 'AutoB_splineS').isChecked()
		print(state, Type, self.sender().objectName())
		active = self.getUi([key + 'B_spline' + i for i in spins])
		data = self.getData(Type)
		
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
			
	
	def polyCut(self):
		'''Обрізка [за різними методами]'''
		Param = ('PolyN', 'PolyP', 'PolyM')
		senderName = self.sender().objectName()
		Type = self.Types[senderName[0]]
		active = [Type] + self.findUi((senderName[0] + i for i in Param),p="value")
		XY = self.getData(active[0])
		discrete = self.getUi('Discrete' ).isChecked()
		AC = self.getUi("processView").isChecked()
		# Межі будемо брати з обраної (графічним методом) ділянки 
		
		print('active', active[4:6])
		data = self.poly_cut(XY, N = active[1], p = active[2],
			m = active[3], AC = AC,  discrete=discrete)
		
		if self.showTmp:
			data,  tmp,  poly = data
		self.updateData(array = data.copy())
		
		if self.showTmp:
			self.ui.mpl.canvas.ax.plot(tmp[0],  tmp[1], '.m',  alpha=0.2,  zorder=1)
			self.ui.mpl.canvas.ax.plot(  poly[0],  poly[1],  'r')
			self.ui.mpl.canvas.draw()
			
	def Average(self):
		'''Усереднення за різними методами'''
		senderName = self.sender().objectName()
		key = senderName[0]
		step = self.getUi(key + 'AverageStep').value()
		XY = self.getData(key)
		M = self.getUi(key+'PolyM').value()
		discrete = self.getUi('Discrete' ).isChecked()
		AC = self.getUi("processView").isChecked()
		Approx = self.getUi(key+'AverageApprox').isChecked()
		data = self.averaging(XY, step=step,	m=M, discrete=discrete,
					AC=AC, Approx=Approx )
		if self.showTmp:
			data, x, y, poly = data
		self.updateData(array = data)
		
		if self.showTmp:
			self.ui.mpl.canvas.ax.plot(x,  y, '.m',  alpha=0.2,  zorder=1)
			if Approx:
				self.ui.mpl.canvas.ax.plot(  poly[0],  poly[1],  'r')
			self.ui.mpl.canvas.draw()
	
	def PolyApprox(self):
		''' Апроксимація поліномом n-го степ. '''
		Type = self.currentType()
		key = self.sender().objectName()[0]
		data = self.getData(Type)
		X, Y = data[:, 0], data[:, 1]
		step = self.getUi(key + 'ApproxStep').value()
		M = self.getUi(key + 'ApproxM').value()
		AC = self.getUi("processView").isChecked()
		piece_wise = self.getUi(key + 'ApproxPiece_wise').isChecked()
		x, y = X.copy(), Y.copy()
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
			Type=data.Type, scale=data.scale))
		
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
		
	def B_spline(self):
		'''інтерполяція b-сплайном'''
		senderName = self.sender().objectName()
		#active =  (Dict[senderName][0],) + self.findChilds(QtGui.QDoubleSpinBox,
		#		Dict[senderName][1:],p = 'value')
		key = senderName[0]
		step, sm, km = (i.value() for i in self.getUi([key+'B_splineStep', 
			key+'B_splineS', key+'B_splineK']))
		XY = self.getData(key)
		AC = self.getUi("processView").isChecked()
		Smooth = self.getUi(key + 'B_splineSmooth').isChecked()
		data = self.b_s(XY, Step=step, sm=sm, km=int(km), AC=AC, Smooth=Smooth)
		if self.showTmp:
			data,  x, y = data
		self.updateData(array  = data)
		
		if self.showTmp:
			self.ui.mpl.canvas.ax.plot(x,  y, '.m',  alpha=0.5,  zorder=1)
			self.ui.mpl.canvas.draw()
			
		
	def Undo(self):
		'''Відкат до попередніх даних'''
		#Dict = {'cUndo' : 0, 'sUndo' : 1, 'rUndo' : 2}
		#senderName = self.sender().objectName()
		index = self.ui.tabWidget.currentIndex()
		Type = index - 1
		if len(self.dataStack[Type])>=2:
			self.updateData(Type=Type, action=-1)
		else:
			self.dataConfigs[Type]['Undo'] = False
			self.sender().setEnabled(False)

	def Reset(self):
		'''Скидання історії'''
		#Dict = {'cReset' : 0, 'sReset' : 1, 'rReset' : 2}
		#senderName = self.sender().objectName()
		#Type = Dict[senderName]
		index = self.ui.tabWidget.currentIndex()
		Type = index - 1
		if len(self.dataStack[Type])>=2:
			self.updateData(Type=Type, action=0)
		else:
			self.dataConfigs[Type]['Reset']=False
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
			self.updateData( array = Array(data, Type = Type, scale=Scale)  )
		except:
			pass
		
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
		Tabs = ( ('tab_2', 'tab_3','tab_4'),
			('tab_3', 'tab_2','tab_4'))
		uiObj = ('XColumn', 'YColumn', 'MColumn', 'MCheck')
		
		senderName = self.sender().objectName()
		key = senderName[0]
		active = [self.Types[key]] + self.findUi( [ i for i in uiObj])
		data = []
		XY = sp.zeros((0,2))
		path = self.Path[active[0]]
		if os.path.exists(path):
			try:
				
				data = sp.loadtxt(path, delimiter=self.settings.getDelimiter())
				'''
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
				'''
				xc = active[1].value()
				yc = active[2].value()
				mc = active[3].value()
				if active[4].checkState():
					XY = sp.array( [data[:,xc], data[:,yc] ]).T / sp.array([data[:,mc], data[:,mc]]).T
				else:
					XY = sp.array( [data[:,xc], data[:,yc] ]).T
				#XY = XY[XY[:,0] != 0]
				#XY = XY[XY[:,1] != 0]
				if getattr(self.ui,'CutForward').isChecked():
					p = sp.where( XY[:,0] == XY[:,0].max())[0][0]
					print(p)
					XY = XY[:p,:]
				XY = XY[sp.argsort(XY[:,0])]
				'''
				XY[:,0] = XY[:,0]/self.filtList[active[0]][0]
				XY[:,1] = XY[:,1]/self.filtList[active[0]][1]
				'''
				self.updateData(array = Array(XY,Type = active[0]), action = 0)
				tabs = self.findUi(Tabs[active[0]])
				tabs[0].setEnabled(True)
				
				if tabs[1].isEnabled():
					tabs[2].setEnabled(True)
			except (ValueError, IOError, IndexError):
				self.mprint("loadData: readError")
		else:  self.mprint('loadData: pathError')
			
	def dataListener(self,Type, action):
		"""Обробка зміни даних"""
		active = self.getData(Type)
		self.mprint("dataChanged: scaleX : %d, scaleY : %d, type : %d, len : %d, action : %d" %\
			  (active.scaleX, active.scaleY ,active.Type, sp.shape(active)[0],action))
		#for i in self.dataStack[Type]:
		#	print(i.scale)
		
		if sp.any(active):
			
			self.AutoB_splineS(Type=Type)
			##### Undo/Reset
			hist = self.dataStack[Type]
			state = False
			if len(hist)>=2:
				state = True
			self.dataConfigs[Type]['Reset'] = state
			self.dataConfigs[Type]['Undo'] = state
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
	def currentType(self):
		Type = self.ui.tabWidget.currentIndex() - 1
		if Type <0:
			Type = self.OPT['defaultTabType']
		return Type
	def getUi(self, attrNames):
		if type(attrNames) in (type([]), type(())):
			return tuple(getattr(self.ui, i) for i in attrNames)
		else:
			return getattr(self.ui, attrNames)
		
	def formatedUpdate(self, data, scale, Type):
		self.updateData(Array(data, scale=scale, Type=Type))

	def mprint(self, m):
		'''Вивід повідомлень в поле статусу'''
		self.ui.statusbar.showMessage(m)
		print(m)
	
	def Plot(self, array):
		self.OPT['defaulTabType'] = array.Type
		self.qcut.Plot(array)
		
	def updateData(self, array = Array(sp.zeros((0,2)),scale=[0,0], Type = 0),
				action = 1, Type = None):
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
		# Запис в історію
		if action == 1:
			if sp.any(array) and sp.shape(array)[1] == 2\
					and sp.shape(array)[0] > 1:
				self.dataStack[Type].append(array)
				emit = True

			else: print('updateData: arrayError',sp.any(array) ,
			            sp.shape(array)[1] == 2 , sp.shape(array)[0] > 1)
		
		# Видалення останнього запису
		elif action == -1 and len(self.dataStack[Type])>=2:
			self.dataStack[Type].pop()
			emit = True
			#self.setActiveLogScale( Type)
		# Скидання історії, або запис першого елемента історії
		elif action == 0:
			print(0)
			if sp.any(array) and sp.shape(array)[1] == 2\
					and sp.shape(array)[0] > 1 and len(self.dataStack[Type])>=1:
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
		# Емітувати повідомлення про зміу даних
		if emit:
			self.data_signal.emit(Type, action)
			self.Plot(self.getData(Type) )
	
	def getData(self,Type):
		if type(Type) == type(''):
			Type = self.Types[Type]
		return self.dataStack[Type][-1].copy()
	
	def getFilters(self, length="532"):
		"""Читання таблиці фільтрів та вибір значень для даної довжини хвилі"""
		filt = sp.loadtxt(self.FiltersPath, dtype="S")
		col = sp.where(filt[0,:]==length)[0][0]
		return dict( zip(filt[1:,0], sp.array(filt[1:,col],dtype="f") ) )
	
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
		self.ui.cFile.clicked.connect(self.getFilePath)
		self.ui.sFile.clicked.connect(self.getFilePath)
		self.ui.cLoad.clicked.connect(self.loadData)
		self.ui.sLoad.clicked.connect(self.loadData)
		self.ui.cPath.textChanged.connect(self.pathTextChanged)
		self.ui.sPath.textChanged.connect(self.pathTextChanged)
		self.ui.tabWidget.currentChanged[int].connect(self.confCurrent)
		self.ui.MCheck.toggled[bool].connect(self.ui.MColumn.setEnabled)
		self.ui.MCheck.toggled[bool].connect(self.ui.MColumn.setEnabled)

		self.ui.Undo.triggered.connect(self.Undo)
		self.ui.Reset.triggered.connect(self.Reset)
		
		self.ui.cPolyOk.clicked.connect(self.polyCut)
		self.ui.sPolyOk.clicked.connect(self.polyCut)
		self.ui.cAverageOk.clicked.connect(self.Average)
		self.ui.sAverageOk.clicked.connect(self.Average)
		self.ui.cPolyApprox.clicked.connect(self.PolyApprox)
		self.ui.sPolyApprox.clicked.connect(self.PolyApprox)
		self.ui.rPolyApprox.clicked.connect(self.PolyApprox)
		
		#self.ui.cMedFilt.clicked.connect(self.medFilt)
		#self.ui.sMedFilt.clicked.connect(self.medFilt)
		#self.ui.rMedFilt.clicked.connect(self.medFilt)
		
		self.ui.cB_splineOk.clicked.connect(self.B_spline)
		self.ui.sB_splineOk.clicked.connect(self.B_spline)
		self.ui.rB_splineOk.clicked.connect(self.B_spline)
		self.ui.rButton.clicked.connect(self.ResEval)
		#self.ui.cAutoInterval.toggled[bool].connect(self.AutoInterval)
		#self.ui.sAutoInterval.toggled[bool].connect(self.AutoInterval)
		#self.ui.rAutoInterval.toggled[bool].connect(self.AutoInterval)
		self.ui.cAutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		self.ui.cAutoB_splineS.toggled[bool].connect(self.connectAutoB_sS)
		self.ui.sAutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		self.ui.sAutoB_splineS.toggled[bool].connect(self.connectAutoB_sS)
		self.ui.rAutoB_splineS.toggled[bool].connect(self.AutoB_splineS)
		self.ui.rAutoB_splineS.toggled[bool].connect(self.connectAutoB_sS)
		
		self.ui.cSave.clicked.connect(self.Save)
		self.ui.sSave.clicked.connect(self.Save)
		self.ui.rSave.clicked.connect(self.Save)
		self.ui.tmpShow.toggled[bool].connect(self.plotTmp)
		self.ui.createProj.triggered.connect(self.createProj)
		
		'''
		self.ui.cFilt.toggled[bool].connect(self.ui.cXFilt.setEnabled)
		self.ui.cFilt.toggled[bool].connect(self.ui.cYFilt.setEnabled)
		self.ui.sFilt.toggled[bool].connect(self.ui.sXFilt.setEnabled)
		self.ui.sFilt.toggled[bool].connect(self.ui.sYFilt.setEnabled)
		'''
		self.ui.cFiltOk.clicked.connect(self.applyFilt)
		self.ui.sFiltOk.clicked.connect(self.applyFilt)
		#self.ui.rEvalType.activated[str].connect(self.interpTypeChanged)
		self.ui.norm_Max.triggered.connect(self.norm_Max)
		self.ui.norm_Point.triggered.connect(self.norm_Point)
		self.ui.norm_FirstPoint.triggered.connect(self.norm_FirstPoint)
		self.ui.settings.triggered.connect(self.settings.show)
		# Масштабування
		self.ui.actionY_X.toggled[bool].connect(self.setNewScale)
		##self.ui.checkY_X.toggled[bool].connect(self.ui.actionY_X.toggle)
		self.ui.actionY_Log10.toggled[bool].connect(self.setNewScale)
		self.ui.actionX_Log10.toggled[bool].connect(self.setNewScale)
		self.ui.rYInPercents.toggled[bool].connect(self.rYInPercents)
		self.ui.movePoint.triggered.connect(self.movePoint)
		self.ui.Close.triggered.connect(self.close)
		#self.close.connect(self.closeEvent)
		#self.ui.LENGTH.currentIndexChanged[str].connect(self.setLength)
		#___________________________		_____________________
		self.data_signal[int,int].connect(self.dataListener)
		self.data_signal[int,int].connect(self.setPrevScale)
		
		#+++++++++++++++++++  Intensity     ++++++++++++++++++++++++++++++++++++++
		self.ui.recalcIntens.triggered[bool].connect(self.recalcIntens)
		#self.ui.typeExp.currentIndexChanged[int].connect(self.typeExp)
		#self.ui.calibr.editingFinished.connect(self.calibrChanged)
		####################  intensDialog  ######################################
		#self.ui.recalcForIntens.clicked.connect(self.recalcForIntens)
		#self.intensDialog.ui.buttonBox.accepted.connect(self.getIntens)
		
		
		#self.ui.tabWidget.doubleClicked.connect(self.toggleTabs)
		self.ui.toggleTabs.toggled.connect(self.toggleTabs)
		self.ui.projList.itemDoubleClicked.connect(self.showProj)
		####################  calibrDialog  ######################################
		#self.calibrDialog.ui.ok.clicked.connect(self.getCalibr)
		#self.ui.recalcCalibr.clicked.connect(self.recalcCalibr)
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!tab widget with hiding!!!!!!!!!!!!!!!!
	def setTool(self,objType, objName): return self.findChild(objType,objName)
	
if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal.SIG_DFL) # Застосування Ctrl+C в терміналі
	app = QtGui.QApplication(sys.argv)
	win = QTR()
	win.show()
	
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	win.setTool(QtGui.QLineEdit,'cPath').setText("/home/kronosua/work/QTR/data/Cr2.dat")
	win.setTool(QtGui.QLineEdit,'sPath').setText("/home/kronosua/work/QTR/data/LCg1pl30.dat")
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	
	sys.exit(app.exec_())
	
