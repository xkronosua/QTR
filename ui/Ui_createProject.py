# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/kronosua/work/QTR/ui/createProject.ui'
#
# Created: Sat Feb  9 23:02:40 2013
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
        Dialog.setWindowModality(QtCore.Qt.WindowModal)
        Dialog.resize(478, 553)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setWindowOpacity(0.5)
        Dialog.setSizeGripEnabled(False)
        Dialog.setModal(False)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.List = QtGui.QTableWidget(Dialog)
        self.List.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked)
        self.List.setDragEnabled(True)
        self.List.setDragDropOverwriteMode(False)
        self.List.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.List.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.List.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.List.setColumnCount(2)
        self.List.setObjectName(_fromUtf8("List"))
        self.List.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.List.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.List.setHorizontalHeaderItem(1, item)
        self.List.horizontalHeader().setVisible(True)
        self.verticalLayout.addWidget(self.List)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.Delete = QtGui.QPushButton(Dialog)
        self.Delete.setObjectName(_fromUtf8("Delete"))
        self.horizontalLayout.addWidget(self.Delete)
        self.Plot = QtGui.QPushButton(Dialog)
        self.Plot.setStyleSheet(_fromUtf8(""))
        self.Plot.setObjectName(_fromUtf8("Plot"))
        self.horizontalLayout.addWidget(self.Plot)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.moveDown = QtGui.QToolButton(Dialog)
        self.moveDown.setArrowType(QtCore.Qt.DownArrow)
        self.moveDown.setObjectName(_fromUtf8("moveDown"))
        self.horizontalLayout.addWidget(self.moveDown)
        self.moveUp = QtGui.QToolButton(Dialog)
        self.moveUp.setArrowType(QtCore.Qt.UpArrow)
        self.moveUp.setObjectName(_fromUtf8("moveUp"))
        self.horizontalLayout.addWidget(self.moveUp)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.Save = QtGui.QPushButton(Dialog)
        self.Save.setObjectName(_fromUtf8("Save"))
        self.horizontalLayout.addWidget(self.Save)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Proj", None, QtGui.QApplication.UnicodeUTF8))
        item = self.List.horizontalHeaderItem(0)
        item.setText(QtGui.QApplication.translate("Dialog", "Назва", None, QtGui.QApplication.UnicodeUTF8))
        item = self.List.horizontalHeaderItem(1)
        item.setText(QtGui.QApplication.translate("Dialog", "Колір", None, QtGui.QApplication.UnicodeUTF8))
        self.Delete.setText(QtGui.QApplication.translate("Dialog", "Видалити", None, QtGui.QApplication.UnicodeUTF8))
        self.Plot.setText(QtGui.QApplication.translate("Dialog", "Побудувати", None, QtGui.QApplication.UnicodeUTF8))
        self.moveDown.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.moveUp.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.Save.setText(QtGui.QApplication.translate("Dialog", "Зберегти", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Dialog = QtGui.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

