
import scipy as np
import matplotlib.pyplot as plt
import sys

from PyQt4 import QtCore, QtGui

from qtdesigner2 import Ui_MplMainWindow

def swap(x,y):
	return y,x

class DesignerMainWindow(QtGui.QMainWindow, Ui_MplMainWindow):
	typeColorDict = ['b', 'g', 'k' ]
	color = 'b'
	tempShape = (0,0)
	Type, logScale = 0, [0,0]
	data_signal = QtCore.pyqtSignal( name = "dataChanged")
	def __init__(self, parent = None):
		
		# initial values for all edited and temp values
		self.data, self.tdata, self.sdata = \
			np.zeros((0,2)), \
			np.zeros((0,2)), \
			np.zeros((0,2))
		
		# define lock variables
		self.lock = 0
		self.dlockx, self.dlocky, self.dlocky_x = 0, 1, 1
		self.issecond = 0
		self.background = None
		#self.y_x = 0
		
		# autoscale
		self.autoScale = True
		
		# standart inharitance
		super(DesignerMainWindow, self).__init__(parent)
		self.setupUi(self)

		# push buttons
		# Plot button
		QtCore.QObject.connect(self.mplactionCut_by_line,
							   QtCore.SIGNAL("triggered()"),
							   self.cut_line)
		QtCore.QObject.connect(self.mplactionCut_by_rect,
							   QtCore.SIGNAL("triggered()"),
							   self.cut_rect)
		QtCore.QObject.connect(self.mplactionPoint,
							   QtCore.SIGNAL("triggered()"),
							   self.cut_point)

		# horisintal sliders
		QtCore.QObject.connect(self.mplhorizontalSlider_2,
							   QtCore.SIGNAL("valueChanged(int)"),
							   self.update_graph)

		# checkboxes
		QtCore.QObject.connect(self.mplcheckBox,
							   QtCore.SIGNAL("stateChanged(int)"),
							   self.set_x_log)

		QtCore.QObject.connect(self.mplcheckBox_2,
							   QtCore.SIGNAL("stateChanged(int)"),
							   self.set_y_log)

		QtCore.QObject.connect(self.mplcheckBox_3,
							   QtCore.SIGNAL("stateChanged(int)"),
							   self.set_y_x)

		QtCore.QObject.connect(self.mplcheckBox_4,
							   QtCore.SIGNAL("stateChanged(int)"),
							   self.set_autoScale)

	###########################################################################
	####################### File parsing routines #############################
	###########################################################################

		
	def set_data(self,Data = np.zeros((0,2))):
		self.tdata = Data.copy()
		self.tempShape = np.shape(self.tdata)
		self.update_graph()
		self.Type = Data.Type
		self.logScale = Data.scale

	def Plot(self,Data = np.zeros((0,2))):
		self.color = self.typeColorDict[Data.Type]
		self.set_data(Data)
		
		#self.Rescale()
	
	def getData(self,pr=""):
		if pr:
			print(pr)

		return self.tdata.copy(), self.Type, self.logScale 
		
	# Rescale
	def Rescale(self):
		
		try:
			XY = self.tdata
			xMargin = ( XY[:,0].max() - XY[:,0].min() ) * 0.05
			yMargin =  ( XY[:,1].max() - XY[:,1].min() ) * 0.05
			
			self.mpl.canvas.ax.set_xlim( (XY[:,0].min() - xMargin,\
				XY[:,0].max() + xMargin) )
			self.mpl.canvas.ax.set_ylim( (XY[:,1].min() - yMargin,\
				XY[:,1].max() + yMargin) )
		except:
			pass
		#self.update_graph()

	###########################################################################
	######################## Main plot routines ###############################
	###########################################################################
	def update_graph(self):
		"""Updates the graph with new X and Y"""
		# TODO: rewrite this routine, to get better performance
		
	
		#self.background = \
		#	self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
		# save current plot variables
		self.dlockx = 0
		self.dlocky = 1
		self.dlocky_x = 1
		if self.autoScale:
			self.Rescale()

		if self.background != None:
			# save initial x and y limits
			self.xl = self.mpl.canvas.ax.get_xlim()
			self.yl = self.mpl.canvas.ax.get_ylim()
			
		# clear the axes
		self.mpl.canvas.ax.clear()
		# plot graph
		self.pltdata, = self.mpl.canvas.ax.plot(self.tdata[:, self.dlockx],\
			self.tdata[:, self.dlocky],self.color + 'o',markersize=self.mplhorizontalSlider_2.value())
		# creating line
		self.line, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--',
											 animated=True
											)
		# creating rectangle
		self.rectab, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--',
											 animated=True)
		self.rectbc, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--',
													 animated=True)
		self.rectcd, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--',
													 animated=True)
		self.rectda, = self.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--',
													 animated=True)
		# TODO: create a circle
		# enable grid
		self.mpl.canvas.ax.grid(True)
		
		
		if self.background != None:
			# set x and y limits
			self.mpl.canvas.ax.set_xlim(self.xl)
			self.mpl.canvas.ax.set_ylim(self.yl)
				
		# log x log y scale
		self.set_x_log(flag=1)
		self.set_y_log(flag=1)
		self.set_y_x(flag=1)
		# force an image redraw
		self.mpl.canvas.draw()
		# copy background
		self.background = \
			self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
		# make edit buttons enabled
		#self.mplactionSave.setEnabled(True)
		#self.mplactionUndo.setEnabled(True)
		# self.mplactionRescale.setEnabled(True)
		#self.mplactionRestore.setEnabled(True)
		self.mplactionCut_by_line.setEnabled(True)
		self.mplactionCut_by_rect.setEnabled(True)
		self.mplactionPoint.setEnabled(True)
		#print(np.shape(self.tdata), np.shape(self.data), np.shape(self.sdata), self.tempShape, self.index)
		if np.shape(self.tdata) != self.tempShape :
			self.tempShape = np.shape(self.tdata)
			self.data_signal.emit()
			#print(self.index)
		

	###########################################################################
	####################### Secondary plot routines ###########################
	###########################################################################
	def set_x_log(self, flag=0):
		"""change X scale (log<=>line)"""
		if self.mplcheckBox.isChecked() == True:
			self.mpl.canvas.ax.set_xscale('log')
			self.xlog = 1
		else :
			self.mpl.canvas.ax.set_xscale('linear')
			self.xlog = 0
		if flag == 1:
			pass
		else:
			self.mpl.canvas.draw()

	def set_y_log(self, flag=0):
		"""change Y scale (log<=>line)"""
		if self.mplcheckBox_2.isChecked() == True:
			self.mpl.canvas.ax.set_yscale('log')
			self.ylog = 1
		else :
			self.mpl.canvas.ax.set_yscale('linear')
			self.ylog = 0
		if flag == 1:
			pass
		else:
			self.mpl.canvas.draw()
	
	def set_y_x(self, flag=0):
		"""change Y scale (Y/x<=>line)"""
		Y = []
		if self.mplcheckBox_3.isChecked() == True:
			Y = self.tdata[:,1] / self.tdata[:,0]
			self.dlocky_x = 1
		elif self.mplcheckBox_3.isChecked() == False and self.dlocky_x == 1:
			Y = self.tdata[:,1] * self.tdata[:,0]
			self.dlocky_x = 0
		if flag == 1:
			pass
		else:
			self.tdata[:,1] = Y
			self.mpl.canvas.draw()
			self.update_graph()
			
	def set_autoScale(self, flag=0):
		"""change Y|X autoscale"""
		if self.mplcheckBox_4.isChecked() == True:
			self.autoScale = True
			#self.ylog = 1
		else :
			self.autoScale = False
			#self.ylog = 0
		if flag == 1:
			pass
		else:
			self.update_graph()
			self.Rescale()
	
	def draw_line(self):
		self.mpl.canvas.ax.figure.canvas.restore_region(self.background)
		self.line.set_xdata([self.x1, self.x2])
		self.line.set_ydata([self.y1, self.y2])
		# redraw artist
		self.mpl.canvas.ax.draw_artist(self.line)
		self.mpl.canvas.ax.figure.canvas.blit(self.mpl.canvas.ax.bbox)

	def draw_rect(self):
		self.mpl.canvas.ax.figure.canvas.restore_region(self.background)
		self.rectab.set_xdata([self.x1, self.x2])
		self.rectab.set_ydata([self.y1, self.y1])
		self.rectbc.set_xdata([self.x1, self.x1])
		self.rectbc.set_ydata([self.y1, self.y2])
		self.rectcd.set_xdata([self.x2, self.x2])
		self.rectcd.set_ydata([self.y1, self.y2])
		self.rectda.set_xdata([self.x1, self.x2])
		self.rectda.set_ydata([self.y2, self.y2])
		# redraw artists
		self.mpl.canvas.ax.draw_artist(self.rectab)
		self.mpl.canvas.ax.draw_artist(self.rectbc)
		self.mpl.canvas.ax.draw_artist(self.rectcd)
		self.mpl.canvas.ax.draw_artist(self.rectda)
		self.mpl.canvas.ax.figure.canvas.blit(self.mpl.canvas.ax.bbox)

	###########################################################################
	############################# Buttons #####################################
	###########################################################################
	'''
	def undo(self):
		"""Restore previous condition"""
		if self.sdata.any():
			self.tdata = self.sdata.copy()
			self.update_graph()
		

	def restore(self):
		"""Restore initial condition"""
		if self.data.any():
			self.tdata = self.data.copy()
			self.update_graph()
	
	def save_file(self):
		"""Save current X Y values"""
		file = QtGui.QFileDialog.getSaveFileName()
		OFileHandler = open(file, 'w')
		tmp1 = self.mplspinBox.value() - 1
		tmp2 = self.mplspinBox_2.value() - 1
		tmp3 = self.mplspinBox_3.value() - 1
		for i in range(len(self.tdata[:,tmp1])):
			OFileHandler.write('{0:10e}\t{1:10e}\n'.format(self.tdata[i,tmp1],
														   self.tdata[i,tmp2])
							  )
		OFileHandler.close()
	'''
	###########################################################################
	############################ Events #######################################
	###########################################################################

	############################## Line #######################################
	def cut_line(self):
		"""start cut the line"""
		self.sdata = self.tdata.copy()
		self.cidpress = self.mpl.canvas.mpl_connect(
				'button_press_event', self.on_press)
		self.cidrelease = self.mpl.canvas.mpl_connect(
				'button_release_event', self.on_release)

	def on_press(self, event):
		"""on button press event for line
		"""
		# copy background
		self.background = \
			self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
		if self.issecond == 0:
			self.x1 = event.xdata
			self.y1 = event.ydata
			self.cidmotion = self.mpl.canvas.mpl_connect(
				   'motion_notify_event', self.on_motion)
			return

		if self.issecond == 1 :
			self.x3 = event.xdata
			self.y3 = event.ydata
			# point swap
			if self.x1 >= self.x2:
				self.x1, self.x2 = swap(self.x1, self.x2)
				self.y1, self.y2 = swap(self.y1, self.y2)
			y = ((self.y2 - self.y1) / (self.x2 - self.x1)) * \
				(self.x3 - self.x2) + self.y2
			if self.y3 >= y:
				# up cut
				index = np.array([], dtype=int)
				for i in range(len(self.tdata[:, 0])):
					x = self.tdata[i, 0]
					y = ((self.y2 - self.y1) / (self.x2 - self.x1)) * \
						(x - self.x2) + self.y2
					if self.tdata[i, 1] >= y and x > self.x1 and x < self.x2:
						index = np.append(index, i)
				self.tdata = np.delete(self.tdata, index, axis=0)
				self.update_graph()
			else:
				#down cut
				index = np.array([], dtype=int)
				for i in range(len(self.tdata[:,0])):
					x = self.tdata[i,0]
					y = ((self.y2 - self.y1) / (self.x2 - self.x1)) * \
						(x - self.x2) + self.y2
					if self.tdata[i, 1] <= y and x > self.x1 and x < self.x2:
						index = np.append(index, i)
				self.tdata = np.delete(self.tdata, index, axis=0)
				self.update_graph()
			self.issecond = 0
			self.mplactionCut_by_line.setChecked(False)
			self.mpl.canvas.mpl_disconnect(self.cidpress)
		return

	def on_motion(self, event):
		'''on motion we will move the rect if the mouse is over us'''
		self.x2 = event.xdata
		self.y2 = event.ydata
		self.draw_line()

	def on_release(self, event):
		'''on release we reset the press data'''
		self.x2 = event.xdata
		self.y2 = event.ydata
		self.issecond = 1
		self.draw_line()
		if self.x1 and self.x2 and self.y1 and self.y2:
			self.mpl.canvas.mpl_disconnect(self.cidmotion)
			self.mpl.canvas.mpl_disconnect(self.cidrelease)

	############################### Rect ####################################
	def cut_rect(self):
		"""start to cut the rect"""
		self.sdata = self.tdata.copy()
		self.cidpress = self.mpl.canvas.mpl_connect(
				'button_press_event', self.on_press2)
		self.cidrelease = self.mpl.canvas.mpl_connect(
				'button_release_event', self.on_release2)

	def on_press2(self, event):
		"""on button press event for rectangle
		"""
		# copy background
		self.background = \
			self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)
		# first press
		if self.issecond == 0:
			self.x1 = event.xdata
			self.y1 = event.ydata
			self.cidmotion = self.mpl.canvas.mpl_connect(
			  'motion_notify_event', self.on_motion2)
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
			if self.y3 <= self.y1 and self.y3 >= self.y2 and self.x3 >= self.x1 and self.x3 <= self.x2 :
				# in cut
				index = np.array([], dtype=int)
				for i in range(len(self.tdata[:,0])):
					x = self.tdata[i, 0]
					y = self.tdata[i, 1]
					if y <= self.y1 and y >= self.y2 and x >= self.x1 and x <= self.x2:
						index = np.append(index, i)
				self.tdata = np.delete(self.tdata, index, axis=0)
				self.update_graph()
			else:
				#out cut
				index = np.array([], dtype=int)
				for i in range(len(self.tdata[:, 0])):
					x = self.tdata[i, 0]
					y = self.tdata[i, 1]
					if x <= self.x1 or y >= self.y1 or x >= self.x2 or y <= self.y2:
						index = np.append(index, i)
				self.tdata = np.delete(self.tdata, index, axis=0)
				self.update_graph()
			self.issecond = 0
			self.mplactionCut_by_rect.setChecked(False)
			self.mpl.canvas.mpl_disconnect(self.cidpress)
		return

	def on_motion2(self, event):
		'''on motion we will move the rect if the mouse is over us'''
		self.x2 = event.xdata
		self.y2 = event.ydata
		self.draw_rect()

	def on_release2(self, event):
		'''on release we reset the press data'''
		self.x2 = event.xdata
		self.y2 = event.ydata
		self.issecond = 1
		self.draw_rect()
		if self.x1 and self.x2 and self.y1 and self.y2:
			self.mpl.canvas.mpl_disconnect(self.cidmotion)
			self.mpl.canvas.mpl_disconnect(self.cidrelease)

	############################### Point ####################################
	# TODO: Point cut
	def cut_point(self):
		"""connect to all the events we need to cut the rect"""
		self.sdata = self.tdata.copy()
		self.cidmotion = self.mpl.canvas.mpl_connect(
				'motion_notify_event', self.on_motion31)
		self.cidpress = self.mpl.canvas.mpl_connect(
				'button_press_event', self.on_press3)

	def on_motion31(self, event):
		# copy background
		self.background = \
			self.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.mpl.canvas.ax.bbox)

	def on_press3(self, event):
		self.mpl.canvas.mpl_disconnect(self.cidmotion)
		self.cidmotion = self.mpl.canvas.mpl_connect(
			'motion_notify_event', self.on_motion32)
		self.mpl.canvas.mpl_disconnect(self.cidpress)
		self.cidrelease = self.mpl.canvas.mpl_connect(
				'button_release_event', self.on_release3)

	def on_motion32(self, event):
		pass

	def on_release3(self, event):
		self.mpl.canvas.mpl_disconnect(self.cidmotion)
		self.mpl.canvas.mpl_disconnect(self.cidrelease)

if __name__ == '__main__' :
	app = QtGui.QApplication(sys.argv)
	dmw = DesignerMainWindow()
	a = np.rand(40,2) * 10
	b = a + np.rand(40,2) * 10
	dmw.Plot(a)
	dmw.show()
	sys.exit(app.exec_())
