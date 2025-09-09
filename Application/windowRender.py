import traceback

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton, QGridLayout, \
    QSizePolicy, QHBoxLayout

import time

from SortingTask import SortingTask

import sys

# Worker Code, will probably nbeed to use this at some point. Python threads also work really so itd dealers choice when
# we get to it
'''class WorkerSignals(QObject):
    textUpdate = pyqtSignal(str)
    animChange = pyqtSignal()

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
        else:
            self.signals.textUpdate.emit("1")
        finally:
            self.signals.animChange.emit()'''




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
        self.resize(1100, 700)

        self.sTask = SortingTask(0.25,1000,3)

        ## Temp
        top = QWidget()
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(8,8,8,8)

        self.grid = taskGrid(240,12,12)

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

################
# IN CODE DOCO #
################

''' 
This here is to put my thoughts and 'documentation' as I do things. Will be removed or moved at a later date
You don't have to do this! This is a messy way to communicate my thoughts as I won't be able to remember them by
next meeting

8/09/2025
Anim idea won't work out, as convenient as it'd be for two reasons
1) hard to make a queue for interruptions for error corrections
2) Anims are basically CSS properties and don't really have the capabilitiy to trigger an event when completed 

Good news! I missed a great feature that solves all of these; QTimers. It's literally a timer lmao

Current Idea:
* Keep track of the current state somehow. Via abstract number or something else. When the timer completes, switch to 
the next stage based on the stored state.

This allows for 'interrupts' where we can make it do some error correction anim. Throughput would be constant if we 
didn't do this so I assume we need to have the error correction take some time.

Two numbers? Current state and prior state. Mainly for interrupt purposes, since the user controls provide another
action that needs to be done before everything, but we don't want to just switch the action and stop the arm
from doing whatever. Prior state is checked after the interrupt/error action is called and then we go back to that after
interrupt completion. 



We can use this to tie pretty much everything to the AdvBoxQueue and a few other anim components. 

Timer (1s)
Box elements move to arm (or to appropriate space on the line) 
Timer (1s)
Arm grabs box and moves to the box. 
Timer (1s) 
Arm moves back to position 
Timer (1s) 
Box elements move to arm

(Not exactly like this, since we likely want the boxes to move to the correct space. Just an illustration of the 
process) 


Currently, timer process is stored on the individual task, so timers can run seperately. Will need to thread tasks
'''
