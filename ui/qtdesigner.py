# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qtdesigner.ui'
#
# Created: Mon May  7 23:45:57 2012
#	  by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


class Ui_MplMainWindow(object):
    def setupUi(self, MplMainWindow):
        MplMainWindow.setObjectName(_fromUtf8("MplMainWindow"))
        MplMainWindow.resize(642, 445)
        self.mplcentralwidget = QtGui.QWidget(MplMainWindow)
        self.mplcentralwidget.setObjectName(_fromUtf8("mplcentralwidget"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.mplcentralwidget)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.mplhorizontalLayout_3 = QtGui.QHBoxLayout()
        self.mplhorizontalLayout_3.setObjectName(_fromUtf8("mplhorizontalLayout_3"))
        self.mpl = MplWidget(self.mplcentralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setObjectName(_fromUtf8("mpl"))
        self.mplhorizontalLayout_3.addWidget(self.mpl)
        self.mplverticalLayout_2 = QtGui.QVBoxLayout()
        self.mplverticalLayout_2.setObjectName(_fromUtf8("mplverticalLayout_2"))
        self.mpllabel_3 = QtGui.QLabel(self.mplcentralwidget)
        self.mpllabel_3.setObjectName(_fromUtf8("mpllabel_3"))
        self.mplverticalLayout_2.addWidget(self.mpllabel_3)
        self.mplhorizontalSlider_2 = QtGui.QSlider(self.mplcentralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mplhorizontalSlider_2.sizePolicy().hasHeightForWidth())
        self.mplhorizontalSlider_2.setSizePolicy(sizePolicy)
        self.mplhorizontalSlider_2.setMinimum(1)
        self.mplhorizontalSlider_2.setMaximum(10)
        self.mplhorizontalSlider_2.setProperty("value", 3)
        self.mplhorizontalSlider_2.setOrientation(QtCore.Qt.Horizontal)
        self.mplhorizontalSlider_2.setObjectName(_fromUtf8("mplhorizontalSlider_2"))
        self.mplverticalLayout_2.addWidget(self.mplhorizontalSlider_2)
        self.mpllabel_2 = QtGui.QLabel(self.mplcentralwidget)
        self.mpllabel_2.setObjectName(_fromUtf8("mpllabel_2"))
        self.mplverticalLayout_2.addWidget(self.mpllabel_2)
        self.mplhorizontalSlider = QtGui.QSlider(self.mplcentralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mplhorizontalSlider.sizePolicy().hasHeightForWidth())
        self.mplhorizontalSlider.setSizePolicy(sizePolicy)
        self.mplhorizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.mplhorizontalSlider.setObjectName(_fromUtf8("mplhorizontalSlider"))
        self.mplverticalLayout_2.addWidget(self.mplhorizontalSlider)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.mplverticalLayout_2.addItem(spacerItem)
        # self.mplpushButton = QtGui.QPushButton(self.mplcentralwidget)
        # self.mplpushButton.setEnabled(False)
        # self.mplpushButton.setObjectName(_fromUtf8("mplpushButton"))
        # self.mplverticalLayout_2.addWidget(self.mplpushButton)
        self.mplverticalLayout = QtGui.QVBoxLayout()
        self.mplverticalLayout.setObjectName(_fromUtf8("mplverticalLayout"))
        self.mplhorizontalLayout_2 = QtGui.QHBoxLayout()
        self.mplhorizontalLayout_2.setObjectName(_fromUtf8("mplhorizontalLayout_2"))
        # self.mplspinBox = QtGui.QSpinBox(self.mplcentralwidget)
        # self.mplspinBox.setEnabled(False)
        # self.mplspinBox.setMinimum(1)
        # self.mplspinBox.setMaximum(4)
        # self.mplspinBox.setObjectName(_fromUtf8("mplspinBox"))
        # self.mplhorizontalLayout_2.addWidget(self.mplspinBox)
        # self.mplspinBox_2 = QtGui.QSpinBox(self.mplcentralwidget)
        # self.mplspinBox_2.setEnabled(False)
        # self.mplspinBox_2.setMinimum(1)
        # self.mplspinBox_2.setMaximum(4)
        # self.mplspinBox_2.setObjectName(_fromUtf8("mplspinBox_2"))
        # self.mplhorizontalLayout_2.addWidget(self.mplspinBox_2)
        self.mplverticalLayout.addLayout(self.mplhorizontalLayout_2)
        self.mplverticalLayout_2.addLayout(self.mplverticalLayout)
        self.mpllabel = QtGui.QLabel(self.mplcentralwidget)
        self.mpllabel.setObjectName(_fromUtf8("mpllabel"))
        self.mplverticalLayout_2.addWidget(self.mpllabel)
        self.mplhorizontalLayout_4 = QtGui.QHBoxLayout()
        self.mplhorizontalLayout_4.setObjectName(_fromUtf8("mplhorizontalLayout_4"))
        self.mplcheckBox = QtGui.QCheckBox(self.mplcentralwidget)
        self.mplcheckBox.setObjectName(_fromUtf8("mplcheckBox"))
        self.mplhorizontalLayout_4.addWidget(self.mplcheckBox)
        self.mplcheckBox_2 = QtGui.QCheckBox(self.mplcentralwidget)
        self.mplcheckBox_2.setObjectName(_fromUtf8("mplcheckBox_2"))
        self.mplhorizontalLayout_4.addWidget(self.mplcheckBox_2)
        # self.mplcheckBox_3 = QtGui.QCheckBox(self.mplcentralwidget)
        # self.mplcheckBox_3.setObjectName(_fromUtf8("mplcheckBox_3"))
        # self.mplhorizontalLayout_5.addWidget(self.mplcheckBox_3)
        self.mplcheckBox_4 = QtGui.QCheckBox(self.mplcentralwidget)
        self.mplcheckBox_4.setObjectName(_fromUtf8("mplcheckBox_4"))
        self.mplcheckBox_4.setChecked(True)
        self.mplhorizontalLayout_2.addWidget(self.mplcheckBox_4)
        self.mplverticalLayout_2.addLayout(self.mplhorizontalLayout_4)
        self.mplhorizontalLayout_3.addLayout(self.mplverticalLayout_2)
        self.verticalLayout_3.addLayout(self.mplhorizontalLayout_3)
        # self.mplverticalLayout_2.addWidget(self.mplcheckBox_3)
        MplMainWindow.setCentralWidget(self.mplcentralwidget)
        self.mplmenubar = QtGui.QMenuBar(MplMainWindow)
        self.mplmenubar.setGeometry(QtCore.QRect(0, 0, 642, 25))
        self.mplmenubar.setObjectName(_fromUtf8("mplmenubar"))
        self.mplmenuFile = QtGui.QMenu(self.mplmenubar)
        self.mplmenuFile.setObjectName(_fromUtf8("mplmenuFile"))
        self.mplmenuEdit = QtGui.QMenu(self.mplmenubar)
        self.mplmenuEdit.setObjectName(_fromUtf8("mplmenuEdit"))
        MplMainWindow.setMenuBar(self.mplmenubar)
        self.toolBar = QtGui.QToolBar(MplMainWindow)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        MplMainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.toolBar_2 = QtGui.QToolBar(MplMainWindow)
        self.toolBar_2.setObjectName(_fromUtf8("toolBar_2"))
        MplMainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar_2)
        # self.mplactionOpen = QtGui.QAction(MplMainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/Very_Basic/folder.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        # self.mplactionOpen.setIcon(icon)
        # self.mplactionOpen.setObjectName(_fromUtf8("mplactionOpen"))
        self.mplactionQuit = QtGui.QAction(MplMainWindow)
        self.mplactionQuit.setObjectName(_fromUtf8("mplactionQuit"))
        # self.mplactionUndo = QtGui.QAction(MplMainWindow)
        # self.mplactionUndo.setEnabled(False)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/Very_Basic/delete.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        # self.mplactionUndo.setIcon(icon1)
        # self.mplactionUndo.setObjectName(_fromUtf8("mplactionUndo"))
        self.mplactionCut_by_line = QtGui.QAction(MplMainWindow)
        self.mplactionCut_by_line.setCheckable(True)
        self.mplactionCut_by_line.setEnabled(False)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8("icons/line.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.mplactionCut_by_line.setIcon(icon2)
        self.mplactionCut_by_line.setObjectName(_fromUtf8("mplactionCut_by_line"))
        self.mplactionCut_by_rect = QtGui.QAction(MplMainWindow)
        self.mplactionCut_by_rect.setCheckable(True)
        self.mplactionCut_by_rect.setChecked(False)
        self.mplactionCut_by_rect.setEnabled(False)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8("icons/rect.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.mplactionCut_by_rect.setIcon(icon3)
        self.mplactionCut_by_rect.setObjectName(_fromUtf8("mplactionCut_by_rect"))
        # self.mplactionSave = QtGui.QAction(MplMainWindow)
        # self.mplactionSave.setEnabled(False)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(_fromUtf8("icons/Very_Basic/save_as.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        # self.mplactionSave.setIcon(icon4)
        # self.mplactionSave.setObjectName(_fromUtf8("mplactionSave"))
        '''# rescale
        self.mplactionRescale = QtGui.QAction(MplMainWindow)
        self.mplactionRescale.setEnabled(False)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(_fromUtf8("icons/Very_Basic/rescale.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.mplactionRescale.setIcon(icon7)
        self.mplactionRescale.setObjectName(_fromUtf8("mplactionRescale"))
        '''
        # self.mplactionRestore = QtGui.QAction(MplMainWindow)
        # self.mplactionRestore.setEnabled(False)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(_fromUtf8("icons/Very_Basic/sinchronize.png")), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
        # self.mplactionRestore.setIcon(icon5)
        # self.mplactionRestore.setObjectName(_fromUtf8("mplactionRestore"))
        self.mplactionPoint = QtGui.QAction(MplMainWindow)
        self.mplactionPoint.setCheckable(True)
        self.mplactionPoint.setEnabled(False)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(_fromUtf8("icons/point.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.mplactionPoint.setIcon(icon6)
        self.mplactionPoint.setObjectName(_fromUtf8("mplactionPoint"))
        # self.mplmenuFile.addAction(self.mplactionOpen)
        # self.mplmenuFile.addSeparator()
        # self.mplmenuFile.addAction(self.mplactionSave)
        # self.mplmenuFile.addSeparator()
        # self.mplmenuFile.addAction(self.mplactionQuit)
        # self.mplmenuEdit.addAction(self.mplactionUndo)
        # self.mplmenuEdit.addAction(self.mplactionRestore)
        ##self.mplmenuEdit.addAction(self.mplactionRescale)

        self.mplmenuEdit.addSeparator()
        self.mplmenuEdit.addAction(self.mplactionCut_by_line)
        self.mplmenuEdit.addAction(self.mplactionCut_by_rect)
        self.mplmenuEdit.addAction(self.mplactionPoint)
        self.mplmenubar.addAction(self.mplmenuFile.menuAction())
        self.mplmenubar.addAction(self.mplmenuEdit.menuAction())
        # self.toolBar.addAction(self.mplactionOpen)
        # self.toolBar.addAction(self.mplactionSave)

        self.toolBar.addSeparator()
        # self.toolBar.addAction(self.mplactionUndo)
        # self.toolBar.addAction(self.mplactionRestore)
        ##self.toolBar.addAction(self.mplactionRescale)

        self.toolBar.addSeparator()
        self.toolBar_2.addAction(self.mplactionCut_by_line)
        self.toolBar_2.addAction(self.mplactionCut_by_rect)
        self.toolBar_2.addAction(self.mplactionPoint)
        self.toolBar_2.addSeparator()

        self.retranslateUi(MplMainWindow)
        QtCore.QMetaObject.connectSlotsByName(MplMainWindow)

    def retranslateUi(self, MplMainWindow):
        MplMainWindow.setWindowTitle(
            QtGui.QApplication.translate("MplMainWindow", "ANOD: QtCut", None, QtGui.QApplication.UnicodeUTF8))
        self.mpllabel_3.setText(
            QtGui.QApplication.translate("MplMainWindow", "Point size:", None, QtGui.QApplication.UnicodeUTF8))
        self.mpllabel_2.setText(
            QtGui.QApplication.translate("MplMainWindow", "Rub size:", None, QtGui.QApplication.UnicodeUTF8))
        # self.mplpushButton.setText(QtGui.QApplication.translate("MplMainWindow", "Plot", None, QtGui.QApplication.UnicodeUTF8))
        self.mpllabel.setText(
            QtGui.QApplication.translate("MplMainWindow", "Log:", None, QtGui.QApplication.UnicodeUTF8))
        self.mplcheckBox.setText(
            QtGui.QApplication.translate("MplMainWindow", "X", None, QtGui.QApplication.UnicodeUTF8))
        self.mplcheckBox_2.setText(
            QtGui.QApplication.translate("MplMainWindow", "Y", None, QtGui.QApplication.UnicodeUTF8))
        # self.mplcheckBox_3.setText(QtGui.QApplication.translate("MplMainWindow", "Y/X", None, QtGui.QApplication.UnicodeUTF8))
        self.mplcheckBox_4.setText(
            QtGui.QApplication.translate("MplMainWindow", "Rescale", None, QtGui.QApplication.UnicodeUTF8))
        self.mplmenuFile.setTitle(
            QtGui.QApplication.translate("MplMainWindow", "File", None, QtGui.QApplication.UnicodeUTF8))
        self.mplmenuEdit.setTitle(
            QtGui.QApplication.translate("MplMainWindow", "Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(
            QtGui.QApplication.translate("MplMainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar_2.setWindowTitle(
            QtGui.QApplication.translate("MplMainWindow", "toolBar_2", None, QtGui.QApplication.UnicodeUTF8))
        # self.mplactionOpen.setText(QtGui.QApplication.translate("MplMainWindow", "Open", None, QtGui.QApplication.UnicodeUTF8))
        self.mplactionQuit.setText(
            QtGui.QApplication.translate("MplMainWindow", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        # self.mplactionUndo.setText(QtGui.QApplication.translate("MplMainWindow", "Undo", None, QtGui.QApplication.UnicodeUTF8))
        self.mplactionCut_by_line.setText(
            QtGui.QApplication.translate("MplMainWindow", "Line", None, QtGui.QApplication.UnicodeUTF8))
        self.mplactionCut_by_rect.setText(
            QtGui.QApplication.translate("MplMainWindow", "Rectangle", None, QtGui.QApplication.UnicodeUTF8))
        # self.mplactionSave.setText(QtGui.QApplication.translate("MplMainWindow", "Save", None, QtGui.QApplication.UnicodeUTF8))
        # self.mplactionRestore.setText(QtGui.QApplication.translate("MplMainWindow", "Restore initial", None, QtGui.QApplication.UnicodeUTF8))
        # self.mplactionRescale.setText(QtGui.QApplication.translate("MplMainWindow", "Rescale", None, QtGui.QApplication.UnicodeUTF8))
        self.mplactionPoint.setText(
            QtGui.QApplication.translate("MplMainWindow", "Point", None, QtGui.QApplication.UnicodeUTF8))


from mplwidget import MplWidget
