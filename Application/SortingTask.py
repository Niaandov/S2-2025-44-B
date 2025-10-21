import random

from PyQt5.QtCore import QTimer, QRect, Qt
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

        # Sorting Task Specific
        self.redError = 0
        self.blueError = 0
        if self.numColours > 2:
            self.greenError = 0


        self.renderWindow = sortingTaskWindow(1920,1080,self, self.numColours)


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


    def updateTask(self, errorRateVal, speed, numColours, distrataction):
        self._speed = speed
        self._errorRate = errorRateVal
        
        if self.numColours > numColours:
            self.renderWindow.updateBoxAmount("remove")
        elif self.numColours < numColours: 
            self.renderWindow.updateBoxAmount("add")
        self.numColours = numColours





    def createNewBox(self):
        colour = self.getRandomColour()
        self.boxList.append(colour)
        self.renderWindow.animState = 0
        self.renderWindow.renderNewBox(colour)


    def stopTimer(self):
        self.renderWindow.animTimer.stop()
    
    def renableTimer(self):
        self.renderWindow.animTimer.start(50)


    def advBoxQueue(self):
        boxLocation = self.boxList[0]

        # Checks for an error
        if self.causeError():
            match self.boxList[0]:
                case "red":
                    self.redError += 1
                    if self.greenError is not None:
                        if random.uniform(0.0, 1.0) >= 0.5:
                            boxLocation = 'blue'
                        else:
                            boxLocation = 'green'
                    else:
                        boxLocation = 'blue'
                    print(self.redError)
                case "blue":
                    self.blueError += 1
                    if self.greenError is not None:
                        if random.uniform(0.0, 1.0) >= 0.5:
                            boxLocation = 'red'
                        else:
                            boxLocation = 'green'
                    else:
                        boxLocation = 'red'
                    print(self.blueError)
                case "green":
                    self.greenError += 1
                    if random.uniform(0.0, 1.0) >= 0.5:
                        boxLocation = 'blue'
                    else:
                        boxLocation = 'red'
                    print(self.greenError)

        print(boxLocation)

        self.renderWindow.checkSortBox(boxLocation, self._speed)

        print(self.boxList)
        self.renderWindow.animState = 1

    def startTask(self):
        print("running!")

        for i in range(1):
            self.createNewBox()

        self.renderWindow.startStuff(self._speed)

    def popBox(self):
        self.boxList.pop(0)


    def getRandomColour(self):

        if self.greenError is not None:
            caseNum = random.randint(0, 2)
        else:
            caseNum = random.randint(0,1)

        match caseNum:
            case 0:
                return "red"
            case 1:
                return "green"
            case 2:
                return "blue"
            case _:
                return "blue"


    def causeError(self):
        # Does this work? Does this make sense, I'll never tell~
        error = self._errorRate + random.uniform(-0.05, 0.05) >= random.uniform(0.0,1.0)
        print(error)
        if error:
            return True
        else:
            return False


class sortingTaskWindow(QFrame):
    def __init__(self, minWidth, minHeight, taskParent, numColours):
        super().__init__()

        self.setObjectName("sortingTask")
        self.setStyleSheet("""QFrame { border: 1px solid #d0d0d0; border-radius: 5px; background: #fafafa;}
        QLabel { font-size: 4vmin;}
        QPushButton { padding: 4px 8px;}""")



        self.setMinimumSize(minWidth, minHeight)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(8)


        ##################
        ## RENDER LOGIC ##
        ##################

        self.minHeight = minHeight
        self.minWidth = minWidth
        self.taskParent = taskParent

        # Uses for Sizing. Everything is sized in terms of the proportion of the current minHeight (or set height)
        # We currently do not dynamically resize the graphic components because it's hard and not really worth
        # doing. Will implement in polish stage if required.
        self.sceneHeight = int(minHeight / 2)
        self.sceneWidth = minWidth


        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor(105, 105, 105)))
        self.scene.setSceneRect(0,0, self.sceneWidth ,int(minHeight / 2))

        # Scale 'constants' for the conveyor and height
        self.conveyorHeight = int(self.sceneHeight / 4)
        self.conveyorTopLocation = int(self.sceneHeight / 2 + self.sceneHeight / 6)
        self.boxHeight = int(self.conveyorHeight / 2)

        conveyor = QGraphicsRectItem(0, self.conveyorTopLocation, self.sceneWidth, self.conveyorHeight)
        conveyor.setBrush(QBrush(QColor(155, 155, 155)))
        conveyor.setZValue(1)
        self.scene.addItem(conveyor)

        # Setup Boxes
        # We always have Red/Blue Boxes so keep them constant

        # For reference, self.sceneWidth / 2 - self.boxHeight/ 2 is the centre of the screen
        centreScreenBox = int(self.sceneWidth /2 - self.boxHeight/2)

        # This is a stupid, stupid and lazy way of doing this. I could be using the proper way of using a function and then creating an array/dict/list/tuple for the x/y of the boxes.
        # Might change this? Works since it's 1) easy. and 2) We have a limited number of boxes
        # Shouldn't have any dips in RAM/CPU time either for alt method
        redBox = QGraphicsRectItem(centreScreenBox + int(centreScreenBox / 2), int(self.conveyorHeight), int(self.boxHeight * 1.15),int(self.boxHeight * 1.15))
        redBox.setBrush(QBrush(QColor(255, 0, 0)))
        conveyor.setZValue(2)
        self.scene.addItem(redBox)
        self.redX = int(centreScreenBox + int(centreScreenBox / 2))
        self.redY = self.conveyorHeight

        blueBox = QGraphicsRectItem(centreScreenBox - int(centreScreenBox / 2), int(self.conveyorHeight),int(self.boxHeight * 1.15), int(self.boxHeight * 1.15))
        blueBox.setBrush(QBrush(QColor(0, 0, 255)))
        conveyor.setZValue(2)
        self.scene.addItem(blueBox)
        self.blueX = int(centreScreenBox - int(centreScreenBox / 2))
        self.blueY = blueBox.y()

        if numColours == 3:
            self.greenBox = QGraphicsRectItem(centreScreenBox, int(self.conveyorHeight), int(self.boxHeight * 1.15),int(self.boxHeight * 1.15))
            self.greenBox.setBrush(QBrush(QColor(0, 255, 0)))
            conveyor.setZValue(2)
            self.scene.addItem(self.greenBox)

            self.greenX = centreScreenBox
            self.greenY = self.conveyorHeight

        # Move to Box varaibles
        # Target is the target x/y for comparison
        # add x/y is the same as distToHalfway
        self.targetX = 0
        self.targetY = self.conveyorHeight
        self.addX = 0
        self.addY = 0


        viewport = QGraphicsView(self.scene)
        viewport.setInteractive(False)
        viewport.setFixedSize(self.sceneWidth,self.sceneHeight)

        viewport.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        viewport.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        root.addWidget(viewport)

        self.boxArray = []
        # 'Stored' box, current box that is in the box pos.
        self.blueSB = None
        self.greenSB = None
        self.redSB = None
        self.toDestroyBox = None

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
        print("Current MinWidth: " + str(self.minWidth) + " current speedValue: " + str(speed))
        self.distToHalfway = int(((self.minWidth/2))  / (speed / 50))

    def renderNewBox(self, colour):

        match colour:
            case "red":
                boxCol = "#ff0000"
            case "green":
                boxCol = "#00ff00"
            case "blue":
                boxCol = "#0000ff"

        tempItem = QGraphicsRectItem(0, self.conveyorTopLocation + self.conveyorHeight / 4, self.boxHeight, self.boxHeight)
        tempItem.setBrush(QBrush(QColor(boxCol)))
        tempItem.setZValue(500)
        self.boxArray.append(tempItem)
        self.scene.addItem(tempItem)

    def moveBox(self, disToMovePerMil):
        for box in self.boxArray:
            
            box.setX(box.x() + disToMovePerMil)

        # Changes state once the box at the front of the conveyor reaches the halfway point
        if(self.boxArray[0].x() == self.sceneWidth / 2):
            self.taskParent.advBoxQueue()

    def doAnimationStep(self):
        match self.animState:
            case 0:
                self.moveBox(self.distToHalfway)
            case 1:
                self.placeholder()

    def placeholder(self):
        heldBox = self.boxArray[0]
        heldBox.setX(heldBox.x() + self.addX)
        heldBox.setY(heldBox.y() - self.addY)

        if abs(heldBox.y() / 2) >= self.targetY and abs(heldBox.x()) >= self.targetX or self.targetX == 463 and abs(heldBox.y() / 2) >= self.targetY and abs(heldBox.x()) <= self.targetX:
           self.taskParent.createNewBox()
           self.boxArray.pop(0)
           self.taskParent.popBox()
           if self.toDestroyBox is not None:
               self.scene.removeItem(self.toDestroyBox)
               self.toDestroyBox = None

    
    def updateBoxAmount(self, mode):
        if mode == "add":
            self.greenBox = QGraphicsRectItem(centreScreenBox, int(self.conveyorHeight), int(self.boxHeight * 1.15),int(self.boxHeight * 1.15))
            self.greenBox.setBrush(QBrush(QColor(0, 255, 0)))
            conveyor.setZValue(2)
            self.scene.addItem(self.greenBox)

            self.greenX = centreScreenBox
            self.greenY = self.conveyorHeight
        elif mode == "remove":
            self.scene.removeItem(self.greenBox)
            self.greenX = None
            self.greenY = None
            if self.greenSB is not None:
                self.scene.removeItem(self.greenSB)
                self.greenSB = None
            


        


    def checkSortBox(self, colour, speed):
        match(colour):
            case "blue":
                self.targetX = self.blueX

                if self.blueSB is not None:
                    self.toDestroyBox = self.blueSB
                    self.blueSB = None

                self.blueSB = self.boxArray[0]
                print("blue")
                print(self.targetX)
            case "red":
                self.targetX = self.redX

                if self.redSB is not None:
                    self.toDestroyBox = self.redSB
                    self.redSB = None

                self.redSB = self.boxArray[0]

            case "green":
                self.targetX = self.greenX

                if self.greenSB is not None:
                    self.toDestroyBox = self.greenSB
                    self.greenSB = None

                self.greenSB = self.boxArray[0]

        self.addX = int(((self.targetX - int(self.sceneWidth / 2 - self.boxHeight / 2))) / (speed / 50))
        self.addY = int(((self.conveyorTopLocation + self.conveyorHeight / 4) - self.targetY)  / (speed / 50))




