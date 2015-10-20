from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg \
    import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
# import the NavigationToolbar Qt4Agg widget
from matplotlib.backends.backend_qt4agg \
    import NavigationToolbar2QTAgg as NavigationToolbar


class MplCanvas(FigureCanvas):
    """Class to represent the FigureCanvas widget"""

    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class MplWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        # initialization of Qt MainWindow widget
        QtGui.QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        # instantiate our Matplotlib canvas widget
        self.vbl = QtGui.QVBoxLayout()
        # instantiate the navigation toolbar
        ntb = NavigationToolbar(self.canvas, parent)
        # pack thse widget into the vertical box
        self.vbl.addWidget(self.canvas)
        self.vbl.addWidget(ntb)
        self.setLayout(self.vbl)
