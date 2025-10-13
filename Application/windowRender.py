import traceback

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton, QGridLayout, \
    QSizePolicy, QHBoxLayout

import time

from SortingTask import SortingTask

import sys


class taskGrid(QWidget):
    def __init__(self, minTileWidth, hgap, vgap):
        super().__init__()
        self.minTileWidth = minTileWidth
        self.hgap = hgap
        self.vgap = vgap
        self._boxes = []

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(12,12,12,12)
        self.grid.setHorizontalSpacing(self.hgap)
        self.grid.setVerticalSpacing(self.vgap)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def addTask(self, task):
        task = task.renderWindow

        task.setParent(self)
        self._boxes.append(task)
        self._relayout()

    def removeTask(self, box):
        if box in self._boxes:
            self._boxes.remove(box)
            box.setParent(None)
            box.deleteLater()
            self._relayout()

    def clear(self):
        for b in list(self._boxes):
            b.setParent(None)
            b.deleteLater()
        self._boxes.clear()
        self._relayout()

    def _columns(self):
        w = max(1, self.width())

        cols = max(1, int((w-self.hgap)//(self.minTileWidth + self.hgap)))
        return cols

    def _relayout(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it and it.widget():
                it.widget().setParent(self)

        cols = self._columns()

        for i, b in enumerate(self._boxes):
            r,c = divmod(i, cols)
            self.grid.addWidget(b,r,c)

        for c in range(cols):
            self.grid.setColumnStretch(c,1)
        self.grid.setRowStretch(self.grid.rowCount(),1)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._relayout()






class testWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitoring Window")
        self.resize(1920, 1080)

        self.sTask = SortingTask(0.25,1000,3,[True, True])

        ## Temp
        top = QWidget()
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(8,8,8,8)

        self.grid = taskGrid(1920,12,12)

        root = QWidget()
        root_l = QVBoxLayout(root)
        root_l.setContentsMargins(0,0,0,0)
        self.setCentralWidget(root)
        root_l.addWidget(top); root_l.addWidget(self.grid)

        self.grid.addTask(self.sTask)

        startButton = QPushButton("Start")
        startButton.clicked.connect(self.sTask.startTask)
        top_l.addWidget(startButton)




app = QApplication(sys.argv)

window = testWindow()
window.show()


# Load bearing force show error. Literally will not give you a buttload of error information if this isn't here
# TF2 Coconut Texture levels of important
sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook









# Everything stops here? Cool whatever
app.exec()
