# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/kronosua/work/QTR/ui/console.ui'
#
# Created: Sun Feb 24 03:10:42 2013
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
        Dialog.resize(400, 300)
        self.horizontalLayout = QtGui.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.editor = QtGui.QPlainTextEdit(Dialog)
        self.editor.setObjectName(_fromUtf8("editor"))
        self.verticalLayout.addWidget(self.editor)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.Exec = QtGui.QPushButton(Dialog)
        self.Exec.setObjectName(_fromUtf8("Exec"))
        self.horizontalLayout_2.addWidget(self.Exec)
        self.Close = QtGui.QPushButton(Dialog)
        self.Close.setObjectName(_fromUtf8("Close"))
        self.horizontalLayout_2.addWidget(self.Close)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Console", None, QtGui.QApplication.UnicodeUTF8))
        self.Exec.setText(QtGui.QApplication.translate("Dialog", "Виконати", None, QtGui.QApplication.UnicodeUTF8))
        self.Close.setText(QtGui.QApplication.translate("Dialog", "Закрити", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Dialog = QtGui.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

