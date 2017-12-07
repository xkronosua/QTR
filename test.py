from PyQt4.QtGui import QWidget, QApplication, QTreeView, QListView, QTextEdit, \
                        QSplitter, QHBoxLayout

import sys

class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        treeView = QTreeView()
        listView = QListView()
        textEdit = QTextEdit()
        splitter = QSplitter(self)

        splitter.addWidget(treeView)
        splitter.addWidget(listView)
        splitter.addWidget(textEdit)

        layout = QHBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
