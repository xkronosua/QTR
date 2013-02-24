
import scipy as np
#import matplotlib.pyplot as plt
#import sys

from PyQt4 import QtCore, QtGui

#from qtdesigner import Ui_MplMainWindow
from ui.Ui_qcut import Ui_Form
def swap(x,y):
	return y,x

class DesignerMainWindow(QtGui.QWidget ):
	typeColorDict = ['b', 'g', 'k' ]
	color = 'b'
	tempShape = (0,0)
	Type, logScale = None, None
	paramKeep = []
	data_signal = QtCore.pyqtSignal( name = "dataChanged")
	autoscale = 0
	x1,x2,x3,x4,y1,y2,y3,y4 = (0.,0.,0.,0.,0.,0.,0.,0.)
	def __init__(self, parent = None):
		
		# initial values for all edited and temp values
		self.data, self.tdata, self.sdata = \
			np.zeros((0,2)), \
			np.zeros((0,2)), \
			np.zeros((0,2))
		
		# define lock variables
		self.lock = 0
		
		self.issecond = 0
		self.background = None
		#self.y_x = 0
		# autoscale
		self.autoscale = True
		
		# standart inharitance

		super(DesignerMainWindow, self).__init__(parent)
		if not parent is None:
			self.ui = self.parent().ui
		else:
			self.ui = Ui_Form()
			self.ui.setupUi(self)
		# push buttons
		# Plot button
		self.ui.mplactionCut_by_line.toggled[bool].connect(self.cut_line)
		self.ui.mplactionCut_by_rect.toggled[bool].connect(self.cut_rect)

		# horisintal sliders
		self.ui.mplhorizontalSlider.setRange(1, 5)
		self.ui.mplhorizontalSlider.valueChanged[int].connect(self.update_graph)

		# checkboxes
		self.ui.xLogScale.toggled[bool].connect(self.set_x_log)

		self.ui.yLogScale.toggled[bool].connect(self.set_y_log)

		

		self.ui.autoScale.toggled[bool].connect(self.set_autoScale)

	###########################################################################
	####################### File parsing routines #############################
	###########################################################################

		
	def set_data(self,Data = np.zeros((0,2)), params = []):
		self.tdata = Data.copy()
		self.tempShape = np.shape(self.tdata)
		self.update_graph()
		if len(params)>=1:
			self.paramKeep = params
		if hasattr(Data, 'Type') and hasattr(Data, 'scale'):
			self.Type = Data.Type
			self.logScale = Data.scale

	def Plot(self,Data = np.zeros((0,2)), params = []):
		if hasattr(Data, 'Type') and hasattr(Data, 'scale'):
			self.color = self.typeColorDict[Data.Type]
		else:
			self.color = self.typeColorDict[1]
		self.set_data(Data, params = params)
		
		#self.Rescale()
	
	def getData(self,pr=""):
		if pr:
			print(pr)
		if not self.Type is None and not self.logScale is None:
			return self.tdata, self.Type, self.logScale 
		elif len(self.paramKeep)>=1:
			return self.tdata, self.paramKeep
		else: return self.tdata
	# Rescale
	def Rescale(self):
		
		try:
			XY = self.tdata
			xMargin = abs( XY[:,0].max() - XY[:,0].min() ) * 0.05
			yMargin =  abs( XY[:,1].max() - XY[:,1].min() ) * 0.05
			
			self.ui.mpl.canvas.ax.set_xlim( (XY[:,0].min() - xMargin,\
				XY[:,0].max() + xMargin) )
			self.ui.mpl.canvas.ax.set_ylim( (XY[:,1].min() - yMargin,\
				XY[:,1].max() + yMargin) )
		except:
			print('QCut: rescaleError')
		#self.update_graph()

	###########################################################################
	######################## Main plot routines ###############################
	###########################################################################
	def update_graph(self):
		"""Updates the graph with new X and Y"""
		# TODO: rewrite this routine, to get better performance
		
	
		#self.background = \
		#	self.ui.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.ui.mpl.canvas.ax.bbox)
		# save current plot variables
		if self.autoscale and np.any(self.tdata):
			self.Rescale()
		
		if self.background != None:
			# save initial x and y limits
			self.xl = self.ui.mpl.canvas.ax.get_xlim()
			self.yl = self.ui.mpl.canvas.ax.get_ylim()
		
		# clear the axes
		self.ui.mpl.canvas.ax.clear()
		# plot graph
		self.pltdata, = self.ui.mpl.canvas.ax.plot(self.tdata[:, 0],\
			self.tdata[:, 1],self.color + 'o',markersize=self.ui.mplhorizontalSlider.value())
		
		if not hasattr(self, 'line'):
			# creating line
			self.line, = self.ui.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--',
											 animated=True)
		if not hasattr(self, 'points'):
			# creating points
			self.points, = self.ui.mpl.canvas.ax.plot([0, 0], [0, 0], 'mo',
											 animated=True, markersize=self.ui.mplhorizontalSlider.value()*2)
		if not hasattr(self.ui, 'rectab') :								
			# creating rectangle
			self.rectab, = self.ui.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--',
												 animated=True)
			self.rectbc, = self.ui.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--',
														 animated=True)
			self.rectcd, = self.ui.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--',
														 animated=True)
			self.rectda, = self.ui.mpl.canvas.ax.plot([0, 0], [0, 0], 'r--',
													 animated=True)
		# TODO: create a circle
		# enable grid
		self.ui.mpl.canvas.ax.grid(True)
		
		
		if self.background != None:
			# set x and y limits
			self.ui.mpl.canvas.ax.set_xlim(self.xl)
			self.ui.mpl.canvas.ax.set_ylim(self.yl)
		
		
		self.set_x_log(self.ui.xLogScale.isChecked(), redraw = False)
		self.set_y_log(self.ui.yLogScale.isChecked(), redraw = False)
		# force an image redraw
		self.ui.mpl.canvas.draw()
		
		# copy background
		self.background = \
			self.ui.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.ui.mpl.canvas.ax.bbox)
		# make edit buttons enabled
		
		self.ui.mplactionCut_by_line.setEnabled(self.background != None)
		self.ui.mplactionCut_by_rect.setEnabled(self.background != None)

		if np.shape(self.tdata) != self.tempShape :
			self.tempShape = np.shape(self.tdata)
			self.data_signal.emit()

		

	###########################################################################
	####################### Secondary plot routines ###########################
	###########################################################################
	def set_x_log(self, flag, redraw = True):
		"""change X scale (log<=>line)"""
		if flag :
			self.ui.mpl.canvas.ax.set_xscale('log')
			self.xlog = 1
		else :
			self.ui.mpl.canvas.ax.set_xscale('linear')
			self.xlog = 0
		if redraw:
			self.ui.mpl.canvas.draw()

	def set_y_log(self, flag, redraw = True):
		"""change Y scale (log<=>line)"""
		if flag :
			self.ui.mpl.canvas.ax.set_yscale('log')
			self.ylog = 1
		else :
			self.ui.mpl.canvas.ax.set_yscale('linear')
			self.ylog = 0
		if redraw:
			self.ui.mpl.canvas.draw()
	
			
	def set_autoScale(self, flag):
		"""change Y|X autoscale"""
		if flag:
			self.autoscale = True
			self.update_graph()
			self.Rescale()
		else :
			self.autoscale = False


	
	def draw_line(self):
		self.ui.mpl.canvas.ax.figure.canvas.restore_region(self.background)
		self.line.set_xdata([self.x1, self.x2])
		self.line.set_ydata([self.y1, self.y2])
		# redraw artist
		self.ui.mpl.canvas.ax.draw_artist(self.line)
		self.ui.mpl.canvas.ax.figure.canvas.blit(self.ui.mpl.canvas.ax.bbox)

	def draw_rect(self):
		self.ui.mpl.canvas.ax.figure.canvas.restore_region(self.background)
		self.rectab.set_xdata([self.x1, self.x2])
		self.rectab.set_ydata([self.y1, self.y1])
		self.rectbc.set_xdata([self.x1, self.x1])
		self.rectbc.set_ydata([self.y1, self.y2])
		self.rectcd.set_xdata([self.x2, self.x2])
		self.rectcd.set_ydata([self.y1, self.y2])
		self.rectda.set_xdata([self.x1, self.x2])
		self.rectda.set_ydata([self.y2, self.y2])
		# redraw artists
		self.ui.mpl.canvas.ax.draw_artist(self.rectab)
		self.ui.mpl.canvas.ax.draw_artist(self.rectbc)
		self.ui.mpl.canvas.ax.draw_artist(self.rectcd)
		self.ui.mpl.canvas.ax.draw_artist(self.rectda)
		self.ui.mpl.canvas.ax.figure.canvas.blit(self.ui.mpl.canvas.ax.bbox)

	###########################################################################
	############################# Buttons #####################################
	###########################################################################
	#------
	###########################################################################
	############################ Events #######################################
	###########################################################################

	############################## Line #######################################
	def cut_line(self,state):
		"""start cut the line"""
		if state:
			
			self.sdata = self.tdata.copy()
			self.cidpress = self.ui.mpl.canvas.mpl_connect(
					'button_press_event', self.on_press)
			self.cidrelease = self.ui.mpl.canvas.mpl_connect(
					'button_release_event', self.on_release)
		else:
			self.issecond = 0
			self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
			self.ui.mpl.canvas.mpl_disconnect(self.cidrelease)
			if hasattr(self,'cidmotion'):
				self.ui.mpl.canvas.mpl_disconnect(self.cidmotion)
			self.update_graph()
		self.ui.mplactionCut_by_rect.setEnabled(not state)
		self.ui.stackedWidget.setEnabled(not state)
			
	def on_press(self, event):
		"""on button press event for line
		"""
		if not event.xdata is None and not event.ydata is None:
			# copy background
			self.background = \
				self.ui.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.ui.mpl.canvas.ax.bbox)
			if self.issecond == 0:
				self.x1 = event.xdata
				self.y1 = event.ydata
				self.cidmotion = self.ui.mpl.canvas.mpl_connect(
					   'motion_notify_event', self.on_motion)
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
					X = self.tdata[:,0]
					Y = self.tdata[:,1]
					yy =  ((self.y2 - self.y1) / (self.x2 - self.x1)) * \
							(X - self.x2) + self.y2
				except:
					y = 0.
				if self.y3 >= y:
					# up cut
					w = (X>=self.x1) * (X<=self.x2) * (Y>=yy) 
					self.tdata = self.tdata[~w,:]
					'''
					index = np.array([], dtype=int)
					for i in range(len(self.tdata[:, 0])):
						x = self.tdata[i, 0]
						y = ((self.y2 - self.y1) / (self.x2 - self.x1)) * \
							(x - self.x2) + self.y2
						if self.tdata[i, 1] >= y and x > self.x1 and x < self.x2:
							index = np.append(index, i)
					self.tdata = np.delete(self.tdata, index, axis=0)
					'''

				else:
					#down cut					
					w = (X>=self.x1) * (X<=self.x2) * (Y<=yy) 
					self.tdata = self.tdata[~w,:]
					'''
					index = np.array([], dtype=int)
					for i in range(len(self.tdata[:,0])):
						x = self.tdata[i,0]
						y = ((self.y2 - self.y1) / (self.x2 - self.x1)) * \
							(x - self.x2) + self.y2
						if self.tdata[i, 1] <= y and x > self.x1 and x < self.x2:
							index = np.append(index, i)
					self.tdata = np.delete(self.tdata, index, axis=0)
					'''
				
				
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
				#self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
				self.ui.mpl.canvas.mpl_disconnect(self.cidmotion)
				self.ui.mpl.canvas.mpl_disconnect(self.cidrelease)
			else:
				self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
		else:
			self.ui.mplactionCut_by_line.setChecked(False)
		
	############################### Rect ####################################
	def cut_rect(self, state):
		if state:
			"""start to cut the rect"""
			self.sdata = self.tdata.copy()
			self.cidpress = self.ui.mpl.canvas.mpl_connect(
					'button_press_event', self.on_press2)
			self.cidrelease = self.ui.mpl.canvas.mpl_connect(
					'button_release_event', self.on_release2)
		else:
			self.issecond = 0
			self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
			self.ui.mpl.canvas.mpl_disconnect(self.cidrelease)
			if hasattr(self,'cidmotion'):
				self.ui.mpl.canvas.mpl_disconnect(self.cidmotion)
			self.update_graph()
		self.ui.mplactionCut_by_line.setEnabled(not state)
		self.ui.stackedWidget.setEnabled(not state)
		
	def on_press2(self, event):
		"""on button press event for rectangle
		"""
		if not event.xdata is None and not event.ydata is None:
			# copy background
			self.background = \
				self.ui.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.ui.mpl.canvas.ax.bbox)
			# first press
			if self.issecond == 0:
				self.x1 = event.xdata
				self.y1 = event.ydata
				
				self.cidmotion = self.ui.mpl.canvas.mpl_connect(
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
				X = self.tdata[:,0]
				Y = self.tdata[:,1]
				w = (X>=self.x1) * (X<=self.x2) * (Y<=self.y1) * (Y>=self.y2)
				if self.y3 <= self.y1 and self.y3 >= self.y2 and self.x3 >= self.x1 and self.x3 <= self.x2 :
					# in cut
					self.tdata = self.tdata[~w,:]
					'''
					index = np.array([], dtype=int)
					for i in range(len(self.tdata[:,0])):
						x = self.tdata[i, 0]
						y = self.tdata[i, 1]
						if y <= self.y1 and y >= self.y2 and x >= self.x1 and x <= self.x2:
							index = np.append(index, i)
					self.tdata = np.delete(self.tdata, index, axis=0)
					'''
				else:
					#out cut
					self.tdata = self.tdata[w,:]
	
					'''
					index = np.array([], dtype=int)
					for i in range(len(self.tdata[:, 0])):
						x = self.tdata[i, 0]
						y = self.tdata[i, 1]
						if x <= self.x1 or y >= self.y1 or x >= self.x2 or y <= self.y2:
							index = np.append(index, i)
					self.tdata = np.delete(self.tdata, index, axis=0)
					'''

				
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
				#self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
				self.ui.mpl.canvas.mpl_disconnect(self.cidmotion)
				self.ui.mpl.canvas.mpl_disconnect(self.cidrelease)
			else:
				self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
		else:
			self.ui.mplactionCut_by_rect.setChecked(False)
		
	'''
	############################### Point ####################################
	# TODO: Point cut
	def cut_point(self):
		"""connect to all the events we need to cut the rect"""
		self.sdata = self.tdata.copy()
		self.cidmotion = self.ui.mpl.canvas.mpl_connect(
				'motion_notify_event', self.on_motion31)
		self.cidpress = self.ui.mpl.canvas.mpl_connect(
				'button_press_event', self.on_press3)

	def on_motion31(self, event):
		# copy background
		self.background = \
			self.ui.mpl.canvas.ax.figure.canvas.copy_from_bbox(self.ui.mpl.canvas.ax.bbox)

	def on_press3(self, event):
		self.ui.mpl.canvas.mpl_disconnect(self.cidmotion)
		self.cidmotion = self.ui.mpl.canvas.mpl_connect(
			'motion_notify_event', self.on_motion32)
		self.ui.mpl.canvas.mpl_disconnect(self.cidpress)
		self.cidrelease = self.ui.mpl.canvas.mpl_connect(
				'button_release_event', self.on_release3)

	def on_motion32(self, event):
		pass

	def on_release3(self, event):
		self.ui.mpl.canvas.mpl_disconnect(self.cidmotion)
		self.ui.mpl.canvas.mpl_disconnect(self.cidrelease)
	'''
'''
if __name__ == '__main__' :
	app = QtGui.QApplication(sys.argv)
	dmw = DesignerMainWindow()
	a = np.rand(40,2) * 10
	b = a + np.rand(40,2) * 10
	dmw.Plot(a)
	dmw.show()
	sys.exit(app.exec_())
'''
