import traceback

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton

import time

from SortingTask import SortingTask

import sys


# I hate this so much hahah
# We are restricted to creating signals and starting stuff AFTER the exec is done, meaning everything will be tied to buttons. This is cool! this is fine! It's not but w/e
# The answer is threading, as always. I was hoping threading was a for-later-performance-increase but its literally required
# GUI is event based, meaning that it is only updated when it has control and when an event is triggered, for most our purposes this fucking SUCKS. Since we can't say 'hey change this' until an entire event is processed.
# So we use threads and processes, trigger our own events when needed

class WorkerSignals(QObject):
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
            self.signals.animChange.emit()

class testWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout()
        mainWidget = QWidget()


        self.testLabel = QLabel("Base")
        font = self.testLabel.font()
        font.setPointSize(20)
        self.testLabel.setFont(font)
        self.testLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)



        self.button = QPushButton("Start")
        self.button.setCheckable(True)
        self.button.clicked.connect(self.startProgram)

        layout.addWidget(self.button)
        layout.addWidget(self.testLabel)
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

        # Stuff for Threading
        self.threadpool = QThreadPool()

    def startProgram(self):
        self.sTask = SortingTask(0.15, 2, 3)
        self.mainLoop()



    def mainLoop(self):
                self.box()

                time.sleep(1)

                self.adv()

                time.sleep(1)



    def box(self):
        self.sTask.createNewBox()
        self.updateText()


    def adv(self):
        self.sTask.advBoxQueue()
        self.updateText()

    def updateText(self):
        self.testLabel.setText(str(len(self.sTask.boxList)))
        self.testLabel.repaint()


app = QApplication(sys.argv)

window = testWindow()
window.show()

sTask = SortingTask(0.15, 2, 3)





sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook









# Everything stops here? Cool whatever
app.exec()

