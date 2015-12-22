import matplotlib
try:
	matplotlib.use('Qt5Agg', force=True)

	from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
	# Python Qt4 bindings for GUI objects
	from PyQt5 import QtGui, QtCore
	# import the NavigationToolbar Qt4Agg widget
	from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
	# import the Qt4Agg FigureCanvas object, that binds Figure to
	# Qt4Agg backend. It also inherits from QWidget
	from PyQt5.QtWidgets import QWidget, QSizePolicy, QToolButton, QVBoxLayout
except:
	matplotlib.use('Qt4Agg', force=True)

	from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
	# Python Qt4 bindings for GUI objects
	from PyQt4 import QtGui, QtCore
	# import the NavigationToolbar Qt4Agg widget
	from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
	# import the Qt4Agg FigureCanvas object, that binds Figure to
	# Qt4Agg backend. It also inherits from QWidget
	from PyQt4.QtGui import QWidget, QSizePolicy, QToolButton, QVBoxLayout

from matplotlib.widgets import SpanSelector

# Matplotlib Figure object
from matplotlib.figure import Figure

import mpl_toolkits.axisartist as axisartist
#				"figure.facecolor": 'white'
style = {
	#'backend': 'qt5agg',

	"font.size": 9.0,

	"figure.subplot.left": 0.0,
	"figure.subplot.right": 1,
	"figure.subplot.bottom": 0.0,
	"figure.subplot.top": 1,
	"figure.subplot.wspace": 0.0,
	"figure.subplot.hspace": 0.0,
	"lines.color": "white",
	"lines.antialiased": True,
	# 'lines.linewidth': 5,
	"patch.edgecolor": "white",
	"patch.facecolor": "white",
	"patch.linewidth": 5,

	"text.color": "white",

	"axes.facecolor": "#000002",
	"axes.edgecolor": "#222222",
	"axes.labelcolor": "green",
	# "axes.spines.color": "white",

	"xtick.color": "white",
	"ytick.color": "white",

	"grid.color": "orange",

	"figure.facecolor": "#000005",
	"figure.edgecolor": "white",

	"contour.negative_linestyle": 'solid',

	"savefig.facecolor": "black",
	"savefig.edgecolor": "black"}
matplotlib.rcParams.update(style)


class MplCanvas(FigureCanvas):
	"""Class to represent the FigureCanvas widget"""

	def __init__(self):
		# setup Matplotlib Figure and Axis
		self.fig = Figure()
		self.ax = self.fig.add_subplot(axisartist.Subplot(self.fig, "111"))

		# self.ax.grid(True)
		# self.ax.axis('off')
		# self.fig.patch.set_visible(False)
		# self.ax.patch.set_visible(False)

		# initialization of the canvas
		FigureCanvas.__init__(self, self.fig)
		# we define the widget as expandable
		FigureCanvas.setSizePolicy(self,
								   QSizePolicy.Expanding,
								   QSizePolicy.Expanding)
		# notify the system of updated policy
		FigureCanvas.updateGeometry(self)

	def draw(self):
		"""
		Draw the figure with Agg, and queue a request
		for a Qt draw.
		"""
		# The Agg draw is done here; delaying it until the paintEvent
		# causes problems with code that uses the result of the
		# draw() to update plot elements.
		FigureCanvas.draw(self)
		self._priv_update()


class vNavigationToolbar(NavigationToolbar):
	def __init__(self, canvas, parent, orientation=QtCore.Qt.Vertical):
		NavigationToolbar.__init__(self, canvas, parent)

		self.setOrientation(orientation)
		self.clearButtons = []
		# Search through existing buttons
		# next use for placement of custom button
		next = None
		for c in self.findChildren(QToolButton):
			if next is None:
				next = c
			# Don't want to see subplots and customize
			if str(c.text()) in ('Subplots', 'Customize'):
				c.defaultAction().setVisible(False)
				continue
			# Need to keep track of pan and zoom buttons
			# Also grab toggled event to clear checked status of picker button
			# if str(c.text()) in ('Pan','Zoom'):
			#	c.toggled.connect(self.clearPicker)
			#	self.clearButtons.append(c)
			#	next=None


class MplWidget(QWidget):
	"""Widget defined in Qt Designer"""

	def __init__(self, parent=None):
		# initialization of Qt MainWindow widget
		QWidget.__init__(self, parent)
		# set the canvas to the Matplotlib widget
		self.canvas = MplCanvas()
		self.ntb = vNavigationToolbar(self.canvas, self)

		# self.mpl.ntb.addWidget(ntbButtons[1])
		# create a vertical box layout
		self.vbl = QVBoxLayout()
		# add mpl widget to the vertical box
		self.vbl.addWidget(self.canvas)
		# self.vbl.addWidget(self.ntb)
		# set the layout to the vertical box
		self.setLayout(self.vbl)
