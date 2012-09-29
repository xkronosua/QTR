#!/usr/bin/python
# _*_ coding: utf-8 _*_
import sys, os
from PyQt4 import QtGui, QtCore, uic
import scipy as sp
from scipy.signal import medfilt
import glue_designer as qc

def poly_cut(X, Y, p, d=0.7, m=6):
	'''	Обрізка вздовж кривої апроксиміції поліномом.
	m	-	степінь полінома
	p	-	ширина смуги
	d	-	коефіцієнт уширення
	'''
	EQ = sp.poly1d( sp.polyfit(X, Y, m) )
	poly_Y = EQ( X )
	condition = ((abs(Y - poly_Y)<(p * ( d + abs(poly_Y/max(poly_Y))))))!=0
	Y_new = Y[ condition ]
	X_new = X[ condition ]
	return X_new, Y_new
	
def averaging(x, y, xi = [], N = 100.):
	'''	Усереднення між заданими вузлами.
	N	-	відсоток від кількості старих вузлів		
	'''
	if not any(xi): 
		xi = sp.linspace(x.min(),x.max(),len(x)*N/100.)
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
				ynew.append(  sp.mean(sp.array([EQ(xi_1[i])] + ynew[-3:])))
			else:
				ynew.append(EQ(xi_1[i]))	

	return xi, sp.array(ynew)
	
def b_s(x, y, xi = [], N = 100., sm = 1100000., km = 5):
	'''	Інтерполяція B-сплайном
	N	-	відсоток вузлів
	sm	-	коефіцієнт згладжування
	km	-	степінь полінома
	'''
	print("B-spline interpolation [s = %.3f, k = %.3f]" % (sm,km))
	if not any(xi):
		xi = sp.linspace(x.min(), x.max(), len(x)*N/100.)
	y_interp = sp.interpolate.UnivariateSpline(x, y, s = sm, k = km)(xi)
	return xi, y_interp
	

class QTR(QtGui.QMainWindow):
	''' Ініціалізація змінних.
	cXXXXXX	-	змінна, що відповідає кросу
	sXXXXXX	-	змінна, що відповідає зразку
	rXXXXXX	-	змінна, що відповідає результату
	'''
	cPath = ""	
	sPath = ""
	
	typeInQcut = ''	# тип даних, що знаходяться в QCut

	dataDict = {'c' : [], 's' : [], 'r' : [[]]}
	indexDict = {'c' : 0, 's' : 0, 'r' : 0}	
	def __init__(self):
		# Створюємо теку для тимчасових файлів
		if not os.path.exists("./.tmp"):
			os.mkdir("./.tmp")
		
		# Завантажуємо графічну форму
		QtGui.QMainWindow.__init__(self)
		self.ui = uic.loadUi('qtr.ui')
		self.ui.show()
		
		'''
		# Вантажимо збережені параметри, якщо такі є
		if os.path.exists('config'):
		'''	


		''' Пов’язування сигнали і слоти'''

		# Get data from Qcut onSave
		self.dmw = qc.DesignerMainWindow()
		QtCore.QObject.connect( self.dmw.mplactionSave, QtCore.SIGNAL('triggered()'), self.getBackFromQcut)
		self.dmw.show()
		
		# Loading Data
		#	choose file		
		self.connect(self.ui.cFile,  QtCore.SIGNAL("clicked()"), self.cFile)
		self.connect(self.ui.sFile,  QtCore.SIGNAL("clicked()"), self.sFile)
		#	load columns
		self.connect(self.ui.cLoad,  QtCore.SIGNAL("clicked()"), self.cLoad)
		self.connect(self.ui.sLoad,  QtCore.SIGNAL("clicked()"), self.sLoad)
		
		
		#-----------------------------------------------------------------------
		
		
		# plot
		self.connect(self.ui.cPlot, QtCore.SIGNAL("clicked()"), self.cPlot)
		self.connect(self.ui.sPlot, QtCore.SIGNAL("clicked()"), self.sPlot)
		self.connect(self.ui.resPlot, QtCore.SIGNAL("clicked()"), self.plotRes)
		
		# Poly cut
		self.connect(self.ui.cPolyOk, QtCore.SIGNAL("clicked()"), self.cPolyCut)
		self.connect(self.ui.sPolyOk, QtCore.SIGNAL("clicked()"), self.sPolyCut)
		
		# B-spline
		self.connect(self.ui.cB_splineOk, QtCore.SIGNAL("clicked()"), self.cB_spline)
		self.connect(self.ui.sB_splineOk, QtCore.SIGNAL("clicked()"), self.sB_spline)
		self.connect(self.ui.resB_splineOk, QtCore.SIGNAL("clicked()"), self.resB_spline)
		
		
		# averaging
		self.connect(self.ui.cAverageOk, QtCore.SIGNAL("clicked()"), self.cAverage)
		self.connect(self.ui.sAverageOk, QtCore.SIGNAL("clicked()"), self.sAverage)
		
		# MedFilt
		self.connect(self.ui.cMedFilt, QtCore.SIGNAL("clicked()"), self.cMedFilt)
		self.connect(self.ui.sMedFilt, QtCore.SIGNAL("clicked()"), self.sMedFilt)
		self.connect(self.ui.resMedFilt, QtCore.SIGNAL("clicked()"), self.resMedFilt)
		
		# Reset
		self.connect(self.ui.cReset, QtCore.SIGNAL("clicked()"), self.cReset)
		self.connect(self.ui.sReset, QtCore.SIGNAL("clicked()"), self.sReset)
		self.connect(self.ui.resReset, QtCore.SIGNAL("clicked()"), self.resReset)
		
		# Undo
		self.connect(self.ui.cUndo, QtCore.SIGNAL("clicked()"), self.cUndo)
		self.connect(self.ui.sUndo, QtCore.SIGNAL("clicked()"), self.sUndo)
		self.connect(self.ui.resUndo, QtCore.SIGNAL("clicked()"), self.resUndo)
		
		# Save files
		self.connect(self.ui.cSave, QtCore.SIGNAL("clicked()"), self.cSave)
		self.connect(self.ui.sSave, QtCore.SIGNAL("clicked()"), self.sSave)
		self.connect(self.ui.resSave, QtCore.SIGNAL("clicked()"), self.resSave)
		
		# Res evaluating
		self.connect(self.ui.resButton, QtCore.SIGNAL("clicked()"), self.ResEval)
		
		# Tab changed
		self.connect(self.ui.tabWidget, QtCore.SIGNAL("currentChanged(int)"), self.plotCurrent)
		#self.connect(self.ui.tabWidget, QtCore.SIGNAL("clicked()"), self.sSave)
		#self.connect(self.ui.tabWidget, QtCore.SIGNAL("clicked()"), self.resSave)
		
		# Remove temp files from ./.tmp
		self.connect(self.ui.Close, QtCore.SIGNAL('clicked()'), QtCore.SLOT('close()'))
		
		# Enabling/disabling M column
		self.connect(self.ui.cMCheck, QtCore.SIGNAL('stateChanged(int)'), self.cMCheck)
		self.connect(self.ui.sMCheck, QtCore.SIGNAL('stateChanged(int)'), self.sMCheck)
		
	'''================================================================================'''
	
	# Enabling/disabling M column
	def cMCheck(self, p):
		if p:
			self.ui.cMColumn.setEnabled(True)
		else:
			self.ui.cMColumn.setEnabled(False)
	def sMCheck(self, p):
		if p:
			self.ui.sMColumn.setEnabled(True)
		else:
			self.ui.sMColumn.setEnabled(False)
	# Get data from Qcut onSave
	def getBackFromQcut(self):
		''' Отримання доних, що змінені вручну в QCut'''
		print( "QCut -> "+str(sp.shape(self.dmw.tdata)))
		self.append( self.dmw.tdata, self.typeInQcut)
	
	# Save
	def cSave(self):	self.Save('c')
	def sSave(self):	self.Save('s')
	def resSave(self):	self.Save('r')
			
	def Save(self, type = 'c'):
		''' Отримання назви файлу з QFileDialog і збереження розділювачем \t'''
		filename = QtGui.QFileDialog.getSaveFileName(self,'Save File', os.getenv('HOME'))
		if filename:
			sp.savetxt(str(filename), self.dataDict[type])
			
	# Reset
	''' Завантаження даних з першого збереження'''
	
	def Reset(self, t = 'c'):
		if self.indexDict[t] > 0:
			self.append(type = t, action = 0) 
				
	def cReset(self):	self.Reset('c')		
	def sReset(self):	self.Reset('s')
	def resReset(self):	self.Reset('r')
	
	# Undo
	''' Завантаження даних з попереднього збереження'''
	def Undo(self, t = 'c'):
		if self.indexDict[t] > 0:
			self.append(type = t, action = -1) 
				
	def cUndo(self):	self.Undo('c')		
	def sUndo(self):	self.Undo('s')
	def resUndo(self):	self.Undo('r')
		
	# Evaluate res
	def ResEval(self):
		""" Обчислюємо результат.
			Якщо розміри масивів не співпадають,
			то усереднюємо довший по вузлах коротшого
		"""
		data = self.dataDict
		if len(data['c']) != len(data['s']):
			activeX = []
			if len(data['c']) < len(data['s']):
				self.Print("Length [c] < [s]. c - active")
				activeX = data['c'][:,0]
				x, y = averaging(data['s'][:,0], data['s'][:,1], xi = activeX)
				res = y/data['c'][:,1]
				
			else: 
				self.Print("Length [c] > [s]. s - active")
				activeX = data['s'][:,0]
				x, y = averaging(data['c'][:,0], data['c'][:,1], xi = activeX)
				res = data['s'][:,1] / y
		else:
			activeX = data['c'][:,0]
			res = data['s'][:,1]/data['c'][:,1]
		self.dataDict['r'] = sp.array([activeX,res]).T
		self.append(self.dataDict['r'], 'r', 2)
		
	# averaging
	''' Усереднення по заданій кількості вузлів (у %)'''
	def cAverage(self):
		XY = self.dataDict['c']
		x, y = averaging(XY[:,0], XY[:,1], N = self.ui.cAverageN.value() )
		self.append( sp.array([x,y]).T, "c")
		
	def sAverage(self):
		XY = self.dataDict['s']
		x, y = averaging(XY[:,0], XY[:,1], N = self.ui.sAverageN.value() )
		self.append( sp.array([x,y]).T , 's' )

	# Median filtering of Y
	def MedFilt(self, size = 3, t = 'c'):
		data = self.dataDict[t]
		data = data[ sp.argsort(data[:,0]) ]
		data[:,1] = medfilt( data[:,1], kernel_size = size)
		self.append( data, type = t )
		
	def cMedFilt(self):	self.MedFilt(self.ui.cMedFiltS.value(), 'c')
	def sMedFilt(self):	self.MedFilt(self.ui.sMedFiltS.value(), 's')
	def resMedFilt(self):	self.MedFilt(self.ui.resMedFiltS.value(), 'r')
	
	# B-spline
	def cB_spline(self):
		XY = self.dataDict['c']
		x, y = b_s(XY[:,0], XY[:,1], N = self.ui.cB_splineN.value(),\
			sm = self.ui.cB_splineS.value(), km = self.ui.cB_splineK.value())
		self.append( sp.array([x,y]).T, 'c')
		print( sp.shape(self.dataDict['c']), " x ",  sp.shape(self.dataDict['s']))
		
	def sB_spline(self):
		XY = self.dataDict['s']
		x, y = b_s(XY[:,0], XY[:,1], N = self.ui.sB_splineN.value(),\
			sm = self.ui.sB_splineS.value(), km = self.ui.sB_splineK.value())
		self.append( sp.array([x,y]).T, 's')
		print( sp.shape(self.dataDict['c']), " x ",  sp.shape(self.dataDict['s']))
		
	def resB_spline(self):
		XY = self.dataDict['r']
		x, y = b_s(XY[:,0], XY[:,1], N = self.ui.resB_splineN.value(),\
			sm = self.ui.resB_splineS.value(), km =  self.ui.resB_splineK.value())
		self.append( sp.array([x,y]).T , 'r')
		print( sp.shape(self.dataDict['c']), " x ",  sp.shape(self.dataDict['s']))
		
	# plot
	def cPlot(self):
		self.dmw.setVisible(True)
		self.dmw.Plot(self.dataDict['c'],'c')
	
	def sPlot(self):
		self.dmw.setVisible(True)
		self.dmw.Plot(self.dataDict['s'],'s')
	
	# plot result
	def plotRes(self):
		self.dmw.setVisible(True)
		self.dmw.Rescale()	# rescale
		self.dmw.Plot(self.dataDict['r'],'r')
	
	# Plot current tab
	def plotCurrent(self, index):
		if index != 0:
			ti = 'csr'
			
			type = ti[index-1]
			# Enabling ploting
			t = False
			if   type == 'c': t = self.ui.cLoad.isEnabled()
			elif type == 's': t = self.ui.sLoad.isEnabled()
			elif self.ui.cLoad.isEnabled() and self.ui.sLoad.isEnabled() and any(self.dataDict['r'][0]):
				t = True
			else: t = False
			
			if not self.dmw.isVisible():
				self.dmw.setVisible(True)
			elif t:
				self.dmw.Plot(self.dataDict[type], type)
			else:
				print('No data.')
				
	# Poly cut
	def cPolyCut(self):
		XY = self.dataDict['c']
		x, y = poly_cut(XY[:,0], XY[:,1], self.ui.cPolyP.value(), self.ui.cPolyD.value(), self.ui.cPolyM.value())
		self.append(sp.array([x,y]).T , 'c')
		print( sp.shape(self.dataDict['c']), " x ",  sp.shape(self.dataDict['s']))
		
	def sPolyCut(self):
		XY = self.dataDict['s']
		x, y = poly_cut(XY[:,0], XY[:,1], self.ui.sPolyP.value(), self.ui.sPolyD.value(), self.ui.sPolyM.value())
		self.append( sp.array([x,y]).T , 's')
		print( sp.shape(self.dataDict['c']), " x ",  sp.shape(self.dataDict['s']))
		
	# Choosing files
	def cFile(self):
		self.fileDialog = QtGui.QFileDialog(self)
		path = str( self.fileDialog.getOpenFileName() )
		if path:
			self.cPath = path
			self.ui.cPath.setText(self.cPath)
			self.ui.cLoad.setEnabled(True)
		
	def sFile(self):
		self.fileDialog = QtGui.QFileDialog(self)
		path = str( self.fileDialog.getOpenFileName() )
		if path:
			self.sPath = path
			self.ui.sPath.setText(path)
			self.ui.sLoad.setEnabled(True)
	
	# Loading files
	def cLoad(self):
		xn = int(self.ui.cXColumn.value())
		yn = int(self.ui.cYColumn.value())
		if self.ui.cMCheck.checkState():
			mn = self.ui.cMColumn.value()
		else: mn = -1
		#----------------------------
		self.dataDict['c'] = self.Load(self.ui.cPath.text(), xn, yn, mn)
		self.append(self.dataDict['c'], 'c', 2)
		
		self.ui.tab_2.setEnabled(True)
		if self.ui.tab_3.isEnabled():
			self.ui.tab_4.setEnabled(True)

		
	def sLoad(self):
		xn = int(self.ui.sXColumn.value())
		yn = int(self.ui.sYColumn.value())
		if self.ui.sMCheck.checkState():
			mn = self.ui.sMColumn.value()
		else: mn = -1
		#----------------------------
		self.dataDict['s'] = self.Load(self.ui.sPath.text(), xn, yn, mn)
		self.append(self.dataDict['s'], 's', 2)
		
		self.ui.tab_3.setEnabled(True)
		if self.ui.tab_2.isEnabled():
			self.ui.tab_4.setEnabled(True)
		
		
	#------------------------------------------------------
	def Load(self, path, xn = 1, yn = 2, mn = -1):
		''' Завантаження вказаних колонок з файлу з сортуванням по X.
		Якщо вибрана колонка множника, то X та Y діляться на нього
		'''
		data = sp.loadtxt(str(path))
		if mn!=-1:
			XY = sp.array([data[:,xn],data[:,yn]]).T/sp.array([data[:,mn],data[:,mn]]).T
			print(	sp.shape(XY), xn, yn, mn)
		else:
			XY = sp.array([data[:,xn],data[:,yn]]).T
			print(	sp.shape(XY), xn, yn)
		XY = XY[XY[:,0] != 0]
		XY = XY[sp.argsort(XY[:,0])]
		return XY
	
	#======================================================	
	
	def append(self, array = [], type = 'c' , action = 1):
		""" Запис в тимчасовий файл даних з масиву
		action = {-1, 0, 1, 2}
		-1	:	undo
		0	:	reset
		1	:	add
		2	:	load (reset + create first file)
		"""
		
		self.typeInQcut = type
		m = action
		if m == 2 or m == 0:
			self.indexDict[type] = 0  
		else:
			self.indexDict[type] += m 
		index = self.indexDict[type]
		if m == 1 or m == 2:
			self.dataDict[type] = array
			sp.save("./.tmp/"+type+"Temp"+str(index),array)
		elif m != 2 : 
			array = sp.load("./.tmp/"+type+"Temp"+str(index) + ".npy",array)
			self.dataDict[type] = array
		else: pass
		# En/disabeling buttons
		
		if type == 'c':
			buttons = self.ui.cUndo, self.ui.cReset
		elif type == 's':
			buttons = self.ui.sUndo, self.ui.sReset
		elif type == 'r':
			buttons = self.ui.resUndo, self.ui.resReset
		else:	pass
		
		if self.indexDict[type] == 0 :
			buttons[0].setEnabled(False)
			buttons[1].setEnabled(False)
			
		elif not buttons[0].isEnabled() or not buttons[1].isEnabled():
			buttons[0].setEnabled(True)
			buttons[1].setEnabled(True)
		else:	pass
		
		if not self.dmw.isVisible():
			self.dmw.setVisible(True)
		else:
			self.dmw.Plot(self.dataDict[type], type)
		self.ui.statusbar.showMessage('\tType [' + type + ']. Size: (' + str(len(array)) + ').')
	
	# Terminal + statusbar print
	def Print(self, message):
		print(message)
		self.ui.statusbar.showMessage(message)
			
	def closeEvent(self, event):
		''' Очищення теки з тимчасовими файлами'''
		self.Print( "Removing temp files from ./.tmp/ ...")
		folder = './.tmp/'
		for the_file in os.listdir(folder):
			file_path = os.path.join(folder, the_file)
			try:
				if os.path.isfile(file_path):
					os.unlink(file_path)
			except( Exception, e):
				self.Print('Tmp removing error')
				print( e)
				
		self.dmw.close()
		app.exit()
		
if __name__ == "__main__":
	
	app = QtGui.QApplication(sys.argv)

	win = QTR()
	sys.exit(app.exec_())



