import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'

matplotlib.rcParams["font.size"] = 9.0



matplotlib.rcParams["figure.subplot.left"] = 0.0
matplotlib.rcParams["figure.subplot.right"] = 1
matplotlib.rcParams["figure.subplot.bottom"] = 0.0
matplotlib.rcParams["figure.subplot.top"] = 1
matplotlib.rcParams["figure.subplot.wspace"] = 0.0  
matplotlib.rcParams["figure.subplot.hspace"] = 0.0  

#matplotlib.rcParams["figure.facecolor"] = 'white'
style = {
				"lines.color": "white",
				#'lines.linewidth': 5,
				"patch.edgecolor": "white",
				"patch.facecolor": "white",
				"patch.linewidth": 5,


				"text.color": "white",

				"axes.facecolor": "#000002",
				"axes.edgecolor": "white",
				"axes.labelcolor": "#fff000",

				"xtick.color": "white",
				"ytick.color": "white",

				"grid.color": "orange",

				"figure.facecolor": "#000005",
				"figure.edgecolor": "white",

				"contour.negative_linestyle" : 'solid',

				"savefig.facecolor": "black",
				"savefig.edgecolor": "black"}
matplotlib.rcParams.update(style)

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# Python Qt4 bindings for GUI objects
from PySide import QtGui,QtCore
# import the NavigationToolbar Qt4Agg widget
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget


# Matplotlib Figure object
from matplotlib.figure import Figure

import mpl_toolkits.axisartist as axisartist

class MplCanvas(FigureCanvas):
	"""Class to represent the FigureCanvas widget"""
	def __init__(self):
		# setup Matplotlib Figure and Axis
		self.fig = Figure()
		self.ax = self.fig.add_subplot(axisartist.Subplot(self.fig, "111"))

		self.ax.grid(True)
		# self.ax.axis('off')
		# self.fig.patch.set_visible(False)
		# self.ax.patch.set_visible(False)

		# initialization of the canvas
		FigureCanvas.__init__(self, self.fig)
		# we define the widget as expandable
		FigureCanvas.setSizePolicy(self,
								   QtGui.QSizePolicy.Expanding,
								   QtGui.QSizePolicy.Expanding)
		# notify the system of updated policy
		FigureCanvas.updateGeometry(self)

class vNavigationToolbar( NavigationToolbar ):



	def __init__(self, canvas, parent, orientation=QtCore.Qt.Vertical ):
		NavigationToolbar.__init__(self,canvas, parent)
		
		self.setOrientation(orientation)
		self.clearButtons=[]
		# Search through existing buttons
		# next use for placement of custom button
		next=None
		for c in self.findChildren(QtGui.QToolButton):
			if next is None:
				next=c
			# Don't want to see subplots and customize
			if str(c.text()) in ('Subplots','Customize'):
				c.defaultAction().setVisible(False)
				continue
			# Need to keep track of pan and zoom buttons
			# Also grab toggled event to clear checked status of picker button
			#if str(c.text()) in ('Pan','Zoom'):
			#	c.toggled.connect(self.clearPicker)
			#	self.clearButtons.append(c)
			#	next=None


class MplWidget(QtGui.QWidget):
	"""Widget defined in Qt Designer"""
	def __init__(self, parent = None):
		# initialization of Qt MainWindow widget
		QtGui.QWidget.__init__(self, parent)
		# set the canvas to the Matplotlib widget
		self.canvas = MplCanvas()
		self.ntb = vNavigationToolbar(self.canvas, self)
		
		#self.mpl.ntb.addWidget(ntbButtons[1])
		# create a vertical box layout
		self.vbl = QtGui.QVBoxLayout()
		# add mpl widget to the vertical box
		self.vbl.addWidget(self.canvas)
		#self.vbl.addWidget(self.ntb)
		# set the layout to the vertical box
		self.setLayout(self.vbl)