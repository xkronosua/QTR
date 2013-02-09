# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/kronosua/work/QTR/ui/qcut.ui'
#
# Created: Sat Feb  9 23:02:39 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(580, 462)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.mpl = MplWidget(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setMaximumSize(QtCore.QSize(821, 630))
        self.mpl.setObjectName(_fromUtf8("mpl"))
        self.verticalLayout.addWidget(self.mpl)
        self.horizontalLayout_22 = QtGui.QHBoxLayout()
        self.horizontalLayout_22.setSpacing(1)
        self.horizontalLayout_22.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.horizontalLayout_22.setObjectName(_fromUtf8("horizontalLayout_22"))
        self.mplactionCut_by_line = QtGui.QPushButton(Form)
        self.mplactionCut_by_line.setCheckable(True)
        self.mplactionCut_by_line.setFlat(True)
        self.mplactionCut_by_line.setObjectName(_fromUtf8("mplactionCut_by_line"))
        self.horizontalLayout_22.addWidget(self.mplactionCut_by_line)
        self.mplactionCut_by_rect = QtGui.QPushButton(Form)
        self.mplactionCut_by_rect.setCheckable(True)
        self.mplactionCut_by_rect.setFlat(True)
        self.mplactionCut_by_rect.setObjectName(_fromUtf8("mplactionCut_by_rect"))
        self.horizontalLayout_22.addWidget(self.mplactionCut_by_rect)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_22.addItem(spacerItem)
        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout_22.addWidget(self.label_2)
        self.mplhorizontalSlider = QtGui.QSlider(Form)
        self.mplhorizontalSlider.setProperty("value", 3)
        self.mplhorizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.mplhorizontalSlider.setObjectName(_fromUtf8("mplhorizontalSlider"))
        self.horizontalLayout_22.addWidget(self.mplhorizontalSlider)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_22.addItem(spacerItem1)
        self.autoScale = QtGui.QCheckBox(Form)
        self.autoScale.setObjectName(_fromUtf8("autoScale"))
        self.horizontalLayout_22.addWidget(self.autoScale)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_22.addItem(spacerItem2)
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_22.addWidget(self.label)
        self.xLogScale = QtGui.QCheckBox(Form)
        self.xLogScale.setObjectName(_fromUtf8("xLogScale"))
        self.horizontalLayout_22.addWidget(self.xLogScale)
        self.yLogScale = QtGui.QCheckBox(Form)
        self.yLogScale.setObjectName(_fromUtf8("yLogScale"))
        self.horizontalLayout_22.addWidget(self.yLogScale)
        self.verticalLayout.addLayout(self.horizontalLayout_22)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.mplactionCut_by_line.setText(QtGui.QApplication.translate("Form", "Лінія", None, QtGui.QApplication.UnicodeUTF8))
        self.mplactionCut_by_rect.setText(QtGui.QApplication.translate("Form", "Прямокутник", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Form", "Розмір точок: ", None, QtGui.QApplication.UnicodeUTF8))
        self.autoScale.setText(QtGui.QApplication.translate("Form", "Автомасштаб", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Form", "Log10:", None, QtGui.QApplication.UnicodeUTF8))
        self.xLogScale.setText(QtGui.QApplication.translate("Form", "X", None, QtGui.QApplication.UnicodeUTF8))
        self.yLogScale.setText(QtGui.QApplication.translate("Form", "Y", None, QtGui.QApplication.UnicodeUTF8))

from mplwidget import MplWidget

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

