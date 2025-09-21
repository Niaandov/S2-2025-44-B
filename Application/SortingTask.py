import random

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QLabel, QFrame, QGraphicsView, QGraphicsScene, QGraphicsRectItem

from Task import Task

class SortingTask(Task):
    def __init__(self, errorRateVal, speed, numColours):
        self._errorRate = errorRateVal
        self._speed = speed
        self.numColours = numColours
        self.boxList = []

        self.programState = 0
        self.previousState = 0

        self.redError = 0
        self.blueError = 0
        if self.numColours > 2:
            self.greenError = 0


        self.renderWindow = sortingTaskWindow(960,1080,1080)


    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = value

    @property
    def errorRate(self):
        return self._errorRate

    @errorRate.setter
    def errorRate(self, value):
        self._errorRate = value


    def createNewBox(self):
        colour = self.getRandomColour()
        self.boxList.append(colour)
        self.renderWindow.animState = 0
        self.programState = 1
        self.renderWindow.renderNewBox(colour)





    def advBoxQueue(self):
        if self.causeError():
            match self.boxList[0]:
                case "#ff0000":
                    self.redError += 1
                    print(self.redError)
                case "#00ff00":
                    self.blueError += 1
                    print(self.blueError)
                case "#0000ff":
                    self.greenError += 1
                    print(self.greenError)

        self.renderWindow.checkSortBox()

        print(self.boxList)
        self.boxList.pop(0)
        self.programState = 0
        self.renderWindow.animState = 1

    def startTask(self):

        for i in range(1):
            self.createNewBox()

        self.stateTimer = QTimer()
        self.stateTimer.timeout.connect(self.nextState)
        self.stateTimer.start(self._speed)

        self.renderWindow.startStuff(self._speed)



    def nextState(self):
        match self.programState:
            case 0:
                self.createNewBox()

            case 1:
                self.advBoxQueue()
            case 2:
                print("Something Special Coming Soon (it's the interrupt state)")

        # Some rendering anim goes here.
        # Probable process is:
            # Get arm into position to 'pick up' the box
            # Change sprite of arm to include a box with a new colour
            # Remove box on conveyor belt
            # Move box into the right hub
            # Enable box sprite in the hub
            # Colour is decided by current thing


    def getRandomColour(self):

        if self.greenError != None:
            caseNum = random.randint(0, 2)
        else:
            caseNum = random.randint(0,1)

        match caseNum:
            case 0:
                return "#ff0000"
            case 1:
                return "#00ff00"
            case 2:
                return "#0000ff"
            case _:
                return "#0000ff"


    def causeError(self):
        # Does this work? Does this make sense, I'll never tell~
        return self._errorRate + random.uniform(-0.05, 0.05) >= random.uniform(0.0,1.0)


class sortingTaskWindow(QFrame):
    def __init__(self, minWidth, minHeight, maxHeight):
        super().__init__()

        self.setObjectName("sortingTask")
        self.setStyleSheet("""QFrame { border: 1px solid #d0d0d0; border-radius: 5px; background: #fafafa;}
        QLabel { font-size: 4vmin;}
        QPushButton { padding: 4px 8px;}""")

        self.minHeight = minHeight
        self.minWidth = minWidth

        self.setMinimumSize(minWidth, minHeight)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(8)


        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor(105, 105, 105)))
        self.scene.setSceneRect(0,0, 1920 ,int(minHeight / 2))

        conveyor = QGraphicsRectItem(0, int((minHeight / 2) - 50), 1920, int(minHeight / 4))
        conveyor.setBrush(QBrush(QColor(155, 155, 155)))
        conveyor.setZValue(1)

        self.scene.addItem(conveyor)


        viewport = QGraphicsView(self.scene)
        viewport.setInteractive(False)
        viewport.setFixedSize(1920,1080)

        root.addWidget(viewport)

        self.boxArray = []
        self.blueBox = None
        self.greenBox = None
        self.redBox = None

        # Anim State:
            # 0 = Move box along line
            # 1 = Move Arm to box position
            # 2 = Move Arm to appropriate box
            # 3 = General interrupt if needed
        self.animState = 0
        self.animTimer = QTimer()
        self.animTimer.timeout.connect(self.doAnimationStep)

        self.distToHalfway = 0

    def startStuff(self, speed):
        self.animTimer.start(50)

        # Calculates the dist per step required to get to the halfway point for the arm
            # (Width / 2 ) / ( Total Steps )
                # (Width / 2) / (speed / timestep [50])
        self.distToHalfway = int(self.minWidth / (speed / 50))

    def renderNewBox(self, colour):
        tempItem = QGraphicsRectItem(0,int((self.minHeight / 2) - 50 + (( self.minHeight / 4 ) / 24)), int(self.minHeight/4) - 20, int(self.minHeight / 4) - 20 )
        tempItem.setBrush(QBrush(QColor(colour)))
        tempItem.setZValue(500)
        self.boxArray.append(tempItem)
        self.scene.addItem(tempItem)

    def moveBox(self, disToMovePerMil):
        for box in self.boxArray:
            box.setX(box.x() + disToMovePerMil)


    def killBox(self):
        self.scene.removeItem(self.boxArray[0])
        self.boxArray.pop(0)


    def doAnimationStep(self):
        match self.animState:
            case 0:
                self.moveBox(self.distToHalfway)
            case 1:
                self.placeholder()

    def placeholder(self):
        self.boxArray[0].setRotation(self.boxArray[0].rotation() + 20)
        self.greenBox = self.boxArray[0]


    def checkSortBox(self):
        if self.greenBox != None:
            self.scene.removeItem(self.greenBox)
            self.killBox()



