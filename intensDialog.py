# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog.ui'
#
# Created: Mon Dec  3 00:44:07 2012
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(563, 136)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.length = QtGui.QDoubleSpinBox(Dialog)
        self.length.setMinimum(0.01)
        self.length.setMaximum(5000.0)
        self.length.setProperty("value", 1064.0)
        self.length.setObjectName(_fromUtf8("length"))
        self.gridLayout.addWidget(self.length, 1, 0, 1, 1)
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 0, 2, 1, 1)
        self.Z = QtGui.QDoubleSpinBox(Dialog)
        self.Z.setMinimum(0.01)
        self.Z.setMaximum(1000.0)
        self.Z.setProperty("value", 15.0)
        self.Z.setObjectName(_fromUtf8("Z"))
        self.gridLayout.addWidget(self.Z, 1, 2, 1, 1)
        self.F = QtGui.QDoubleSpinBox(Dialog)
        self.F.setMinimum(0.01)
        self.F.setMaximum(1000.0)
        self.F.setProperty("value", 8.0)
        self.F.setObjectName(_fromUtf8("F"))
        self.gridLayout.addWidget(self.F, 1, 1, 1, 1)
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_5 = QtGui.QLabel(Dialog)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 0, 3, 1, 1)
        self.R = QtGui.QDoubleSpinBox(Dialog)
        self.R.setMinimum(0.01)
        self.R.setMaximum(1000.0)
        self.R.setProperty("value", 25.0)
        self.R.setObjectName(_fromUtf8("R"))
        self.gridLayout.addWidget(self.R, 1, 3, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.calc = QtGui.QPushButton(Dialog)
        self.calc.setObjectName(_fromUtf8("calc"))
        self.verticalLayout.addWidget(self.calc)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_4 = QtGui.QLabel(Dialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.horizontalLayout.addWidget(self.label_4)
        self.res = QtGui.QLineEdit(Dialog)
        self.res.setReadOnly(True)
        self.res.setObjectName(_fromUtf8("res"))
        self.horizontalLayout.addWidget(self.res)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "intensDialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "Відстань від лінзи, см", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "Фокусна відстань, см", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Довж. хвилі, нм", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("Dialog", "Радіус, пучка, px (25 мкм)", None, QtGui.QApplication.UnicodeUTF8))
        self.calc.setText(QtGui.QApplication.translate("Dialog", "Обчислити", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Dialog", "Результат:", None, QtGui.QApplication.UnicodeUTF8))

