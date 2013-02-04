# _*_ coding: utf-8 _*_
from ui.Ui_createProject import Ui_Dialog
from PyQt4 import QtGui, QtCore
import sys
import scipy as sp
#from setName import NameDialog
#import os
import csv
import random
from glue_designer import DesignerMainWindow

class ProjectDialog(QtGui.QDialog):
	
	dataList = {}
	tabLen = 0
	editedText = ''
	projPath = './data/newProj.dat'
	projName = ''
	def __init__(self, parent=None, path='./newProj.dat', name='newProj'):
		super(ProjectDialog, self).__init__(parent)
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		self.uiConnect()
		self.projPath = path
		self.setWindowTitle(path)
		self.ui.List.setColumnWidth(0, 250)
		self.ui.List.setColumnWidth(1, 50)
		self.fileDialog = QtGui.QFileDialog(self)
		self.qcut = DesignerMainWindow()
		
		if parent:
			while hasattr(parent.ui, name):
				if name[-1].isdigit():
					name = name[:-1] + str(int(name[-1])+1)
				else: name += '0'
				
			print(hasattr(parent.ui, name))
			self.projName = name
			self.addAction = QtGui.QAction(parent)
			self.addAction.setObjectName('add_' + name)
			self.showAction = QtGui.QAction(parent)
			self.showAction.setObjectName('show_'+name)
			
			print(self.addAction.objectName())
			self.addAction.setText(path)
			self.showAction.setText(path)
			
			parent.ui.projects.addAction(self.showAction)
			parent.ui.addToProjMenu.addAction(self.addAction)
			
			self.addAction.triggered.connect(parent.addToProj)
			self.showAction.triggered.connect(self.show)
			
	def randomColor(self):
		red = random.randint(0, 250)
		green = random.randint(0, 250)
		blue = random.randint(0, 250)
		alpha = 250
		return QtGui.QColor(red, green, blue, alpha)
	
	
	def addToList(self, array, name=''):
		if not name:
			name = 'new'
		while name in self.dataList.keys():
			if name[-1].isdigit():
				name = name[:-1] + str(int(name[-1])+1)
			else: name += '0'
		
		self.dataList.update({name:array})
		self.tabLen += 1
		self.ui.List.setRowCount(self.tabLen)
		
		newItem = QtGui.QTableWidgetItem(name)
		self.ui.List.setItem(self.tabLen - 1, 0, newItem)
		
		color = QtGui.QTableWidgetItem()
		brush = QtGui.QBrush(self.randomColor())
		brush.setStyle(QtCore.Qt.SolidPattern)
		color.setBackground(brush)
		color.setFlags(QtCore.Qt.ItemIsEnabled)
		self.ui.List.setItem(self.tabLen - 1, 1, color)
		#self.ui.List.setCellWidget(self.tabLen-1, 1, color)
		#self.ui.List.addItem(name)
			
	def Delete(self):
		#try:
		
		selected = self.ui.List.selectionModel().selectedIndexes()
		rows = []
		for i in selected:
			rows.append(i.row())
			name = self.ui.List.item(i.row(), 0).text()
			del self.dataList[name]
			print(self.dataList.keys(), name)
			#self.ui.List.removeRow(i.row())
			self.tabLen -= 1
		
		for i in rows[::-1]:
			self.ui.List.removeRow(i)
		#except AttributeError:
		#	pass
		
	def nameEdited(self, item):
		if item.column() == 0 and self.editedText:
			print(self.editedText, item.text())
			self.dataList[item.text()] = self.dataList[self.editedText]
			del self.dataList[self.editedText]
			
	def editItem(self, clicked):
		if clicked.column() == 0:
			item = self.ui.List.item(clicked.row(), 0)
			print(item.text())
			self.ui.List.editItem(item)
			self.editedText = item.text()
			'''
			item = self.ui.List.item(clicked.row(), 0)
			old_name = item.text()
			setName = NameDialog(name=old_name)
			setName.exec_()
			new_name = setName.name
			print (new_name)
			item.setText(new_name)
			self.dataList[new_name] = self.dataList[old_name]
			del self.dataList[old_name]
			'''
			
		if clicked.column() == 1:
			col = QtGui.QColorDialog.getColor()
			self.ui.List.item(clicked.row(), 1).setBackground(col)
			
	def Plot(self):
		selected = self.ui.List.selectionModel().selectedIndexes()
		tmp = []
		for i in selected:
			color = self.ui.List.item(i.row(), 1).background().color().name()
			#color = self.ui.List.item(i.row(), 1).background().color().getRgb()
			#color = [i/1000. for i in color]
			name = self.ui.List.item(i.row(), 0).text()
			tmp.append([name, color])
		
		self.qcut.show()
		self.qcut.update_graph()
		for i in tmp:
			data = self.dataList[i[0]]
			self.qcut.ui.mpl.canvas.ax.plot(data[:, 0], data[:, 1],
				marker='o', linestyle='', color=i[1])
		self.qcut.ui.mpl.canvas.draw()
		self.qcut.Rescale()
			
	def Save(self):
		filename = self.fileDialog.getSaveFileName(self,	'Save File', self.projPath)
		if filename:
			self.projPath = filename
			self.addAction.setText(filename)
			self.showAction.setText(filename)
			
			self.setWindowTitle(filename)
			max_len = 0
			keys = []#self.dataList.keys()
			for i in range(self.ui.List.rowCount()):
				keys.append(self.ui.List.item(i, 0).text())
			headers = []
			print(keys)
			for i in keys:
				max_len = max(max_len, len(self.dataList[i]))
				headers += ['#X-' + i, '#Y-' + i]
			f = open(filename, 'w')
			writer = csv.writer(f, delimiter=' ')
			
			writer.writerow(headers)
			for i in range(max_len):
				row = []
				for j in keys:
					val = [sp.nan, sp.nan]
					if len(self.dataList[j]) == max_len or i< len(self.dataList[j]):
						val = self.dataList[j][i, :].tolist()
					row += val
				writer.writerow(row)
			f.close()
			
	
	def Move(self):
		action = self.sender().objectName()[4:]
		if action == "Down":
			row = self.ui.List.currentRow()
			column = self.ui.List.currentColumn();
			if row < self.ui.List.rowCount()-1:
				self.ui.List.insertRow(row+2)
				for i in range(self.ui.List.columnCount()):
					self.ui.List.setItem(row+2,i,self.ui.List.takeItem(row,i))
					self.ui.List.setCurrentCell(row+2,column)
				self.ui.List.removeRow(row)        


		if action == "Up":    
			row = self.ui.List.currentRow()
			column = self.ui.List.currentColumn();
			if row > 0:
				self.ui.List.insertRow(row-1)
				for i in range(self.ui.List.columnCount()):
				   self.ui.List.setItem(row-1,i,self.ui.List.takeItem(row+1,i))
				   self.ui.List.setCurrentCell(row-1,column)
				self.ui.List.removeRow(row+1)     
	
	def uiConnect(self):
		self.ui.Delete.clicked.connect(self.Delete)
		self.ui.Save.clicked.connect(self.Save)
		self.ui.List.doubleClicked.connect(self.editItem)
		self.ui.List.itemChanged.connect(self.nameEdited)
		self.ui.Plot.clicked.connect(self.Plot)
		self.ui.moveUp.clicked.connect(self.Move)
		self.ui.moveDown.clicked.connect(self.Move)
		
if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	win = ProjectDialog()
	win.addToList(sp.rand(5, 2), name='c')
	win.addToList(sp.rand(15, 2), name='s')
	win.addToList(sp.rand(10, 2), name='r')
	win.show()
	sys.exit(app.exec_())
