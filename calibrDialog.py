# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'calibr.ui'
#
# Created: Mon Dec  3 00:44:05 2012
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
        Dialog.resize(404, 260)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.namesList = QtGui.QListWidget(Dialog)
        self.namesList.setObjectName(_fromUtf8("namesList"))
        self.verticalLayout.addWidget(self.namesList)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.file = QtGui.QPushButton(Dialog)
        self.file.setObjectName(_fromUtf8("file"))
        self.horizontalLayout.addWidget(self.file)
        self.calc = QtGui.QPushButton(Dialog)
        self.calc.setObjectName(_fromUtf8("calc"))
        self.horizontalLayout.addWidget(self.calc)
        self.res = QtGui.QLineEdit(Dialog)
        self.res.setReadOnly(True)
        self.res.setObjectName(_fromUtf8("res"))
        self.horizontalLayout.addWidget(self.res)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.ok = QtGui.QPushButton(Dialog)
        self.ok.setObjectName(_fromUtf8("ok"))
        self.verticalLayout.addWidget(self.ok)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.file.setText(QtGui.QApplication.translate("Dialog", "Вибрати", None, QtGui.QApplication.UnicodeUTF8))
        self.calc.setText(QtGui.QApplication.translate("Dialog", "Обчислити", None, QtGui.QApplication.UnicodeUTF8))
        self.ok.setText(QtGui.QApplication.translate("Dialog", "Файно", None, QtGui.QApplication.UnicodeUTF8))

