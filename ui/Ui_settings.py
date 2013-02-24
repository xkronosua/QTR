# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/kronosua/work/QTR/ui/settings.ui'
#
# Created: Sun Feb 24 03:10:41 2013
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
        Dialog.resize(585, 327)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabWidget = QtGui.QTabWidget(Dialog)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.main = QtGui.QWidget()
        self.main.setObjectName(_fromUtf8("main"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.main)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label_32 = QtGui.QLabel(self.main)
        self.label_32.setObjectName(_fromUtf8("label_32"))
        self.horizontalLayout_2.addWidget(self.label_32)
        self.length = QtGui.QComboBox(self.main)
        self.length.setObjectName(_fromUtf8("length"))
        self.length.addItem(_fromUtf8(""))
        self.length.addItem(_fromUtf8(""))
        self.length.addItem(_fromUtf8(""))
        self.horizontalLayout_2.addWidget(self.length)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.label_6 = QtGui.QLabel(self.main)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.horizontalLayout_4.addWidget(self.label_6)
        self.typeexp = QtGui.QComboBox(self.main)
        self.typeexp.setObjectName(_fromUtf8("typeexp"))
        self.typeexp.addItem(_fromUtf8(""))
        self.typeexp.addItem(_fromUtf8(""))
        self.horizontalLayout_4.addWidget(self.typeexp)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.tabWidget.addTab(self.main, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(200, -1, -1, -1)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.Close = QtGui.QPushButton(Dialog)
        self.Close.setObjectName(_fromUtf8("Close"))
        self.horizontalLayout.addWidget(self.Close)
        self.Ok = QtGui.QPushButton(Dialog)
        self.Ok.setObjectName(_fromUtf8("Ok"))
        self.horizontalLayout.addWidget(self.Ok)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_32.setText(QtGui.QApplication.translate("Dialog", "Довжина хвилі: ", None, QtGui.QApplication.UnicodeUTF8))
        self.length.setItemText(0, QtGui.QApplication.translate("Dialog", "1064", None, QtGui.QApplication.UnicodeUTF8))
        self.length.setItemText(1, QtGui.QApplication.translate("Dialog", "532", None, QtGui.QApplication.UnicodeUTF8))
        self.length.setItemText(2, QtGui.QApplication.translate("Dialog", "633", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("Dialog", "Тип експерименту:", None, QtGui.QApplication.UnicodeUTF8))
        self.typeexp.setItemText(0, QtGui.QApplication.translate("Dialog", "CW", None, QtGui.QApplication.UnicodeUTF8))
        self.typeexp.setItemText(1, QtGui.QApplication.translate("Dialog", "PICO", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.main), QtGui.QApplication.translate("Dialog", "Основне", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("Dialog", "Tab 2", None, QtGui.QApplication.UnicodeUTF8))
        self.Close.setText(QtGui.QApplication.translate("Dialog", "Закрити", None, QtGui.QApplication.UnicodeUTF8))
        self.Ok.setText(QtGui.QApplication.translate("Dialog", "Ok", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Dialog = QtGui.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

