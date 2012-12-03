# _*_ coding: utf-8 _*_
from intensDialog import Ui_Dialog
from PyQt4 import QtGui, QtCore, uic
from math import pi, sqrt
class IntensDialog(QtGui.QDialog):
	Ai2 = 0.
	def __init__(self):
		super(IntensDialog, self).__init__()
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		self.uiConnect()
		
	def calcClicked(self):
		z, length, f, Ae = self.getValue(("Z", "length", "F", "R"))
		Ae *= 25*10**-4
		self.Ai2 = 2*Ae**2*((1-z/f)**2 + (z*length*10**-7/pi/Ae**2)**2)/4

		if self.Ai2:
			self.ui.res.setText(str(sqrt(self.Ai2)))
		## парарапаваілваопівлаормидіяваропфіджмиоіжмгіпимжівгпмцзжкамгріважмгп
	
	def getValue(self, names):
		return (getattr(self.ui, i).value() for i in names)
	def uiConnect(self):
		self.ui.buttonBox.rejected.connect(self.close)
		self.ui.calc.clicked.connect(self.calcClicked)