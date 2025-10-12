import random

from PyQt5.QtCore import QTimer, QRect, Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QLabel, QPushButton, QGraphicsTextItem

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

        self.errorBox = None
        self.correctBox = None


        self.renderWindow = sortingTaskWindow(1920,1080,self, self.numColours)
        self.renderWindow.speed = self._speed



    def createNewBox(self):
        colour = self.getRandomColour()
        self.boxList.append(colour)
        self.renderWindow.animState = 0
        self.renderWindow.renderNewBox(colour)





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

                case "blue":
                    self.blueError += 1
                    if self.greenError is not None:
                        if random.uniform(0.0, 1.0) >= 0.5:
                            boxLocation = 'red'
                        else:
                            boxLocation = 'green'
                    else:
                        boxLocation = 'red'

                case "green":
                    self.greenError += 1
                    if random.uniform(0.0, 1.0) >= 0.5:
                        boxLocation = 'blue'
                    else:
                        boxLocation = 'red'


 

        self.renderWindow.checkSortBox(boxLocation)


        self.renderWindow.animState = 1

    def startTask(self):

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


    def defineErrorBox(self, boxColour):
        self.errorBox = boxColour



        if self.correctBox is not None:
            self.correctionInterrupt()

    def defineCorrectionBox(self, boxColour):
        self.correctBox = boxColour



        if self.errorBox is not None:
            self.correctionInterrupt()

    def correctionInterrupt(self):
            self.renderWindow.errorColour = self.errorBox
            self.renderWindow.correctColour = self.correctBox
            self.renderWindow.interrupt = True



    def causeError(self):
        # Does this work? Does this make sense, I'll never tell~
        error = self._errorRate + random.uniform(-0.05, 0.05) >= random.uniform(0.0,1.0)
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


        ########################
        ## SORTING BIN SET UP ##
        ########################

        
        # For reference, self.sceneWidth / 2 - self.boxHeight/ 2 is the centre of the screen
        centreScreenBox = int(self.sceneWidth /2 - self.boxHeight/2) - + self.boxHeight * 1.15 / 16

        # Done manually. 
                # Create box, set colour, add item to seen, set X + Y transform to keep origin consistent

        # Red
        redBox = QGraphicsRectItem(0, 0, int(self.boxHeight * 1.15),int(self.boxHeight * 1.15))
        redBox.setBrush(QBrush(QColor(255, 0, 0)))
        
        
        redBox.setX(centreScreenBox + int(centreScreenBox / 2))
        redBox.setY(int(self.conveyorHeight))
        
        self.scene.addItem(redBox)
        # We only use [colour]X values to set targets, so we had an offset here to make sure the box appears in the centre of the box
        self.redX = int(centreScreenBox + int(centreScreenBox / 2)) + self.boxHeight * 1.15 / 15
        self.redY = redBox.y()

        # Blue
        blueBox = QGraphicsRectItem(0, 0, int(self.boxHeight * 1.15), int(self.boxHeight * 1.15))
        blueBox.setBrush(QBrush(QColor(0, 0, 255)))

        blueBox.setX(centreScreenBox - int(centreScreenBox / 2)) 
        blueBox.setY(int(self.conveyorHeight))

        self.scene.addItem(blueBox)
        self.blueX = int(centreScreenBox - int(centreScreenBox / 2))  + self.boxHeight * 1.15 / 15
        self.blueY = blueBox.y()

        # If we have more than three boxes. Yes this could have been done in a for loop for implementing more than 3 boxes and colours but
        # Don't need to, don't want to, won't do
        if numColours == 3:
            greenBox = QGraphicsRectItem(0, 0, int(self.boxHeight * 1.15),int(self.boxHeight * 1.15))
            greenBox.setBrush(QBrush(QColor(0, 255, 0)))

            greenBox.setX(centreScreenBox)
            greenBox.setY(int(self.conveyorHeight))

            self.scene.addItem(greenBox)

            self.greenX = centreScreenBox
            self.greenY = greenBox.y()




        # Move to Box varaibles
        # Target is the target x/y for comparison
        # add x/y is the same as distToHalfway
        self.targetX = 0
        self.targetY = self.conveyorHeight + int(self.boxHeight * 1.15) / 15
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
        self.heldBox = None

        # Anim State:
            # 0 = Move box along line
            # 1 = Move Arm to box position
            # 2 = Move Arm to appropriate box
            # 3 = General interrupt if needed
        self.animState = 0
        self.animTimer = QTimer()
        self.animTimer.timeout.connect(self.doAnimationStep)

        self.distToHalfway = 0
        self.priorState = None
        self.interrupt = False
        self.errorColour = None
        self.correctedColour = None
        self.speed = None

        ############
        # Controls #
        ############
        errorLabel = QLabel("Box With Error")
        errorLabel.setAlignment(Qt.AlignCenter)
        root.addWidget(errorLabel)

        errorLayout = QHBoxLayout(self)
        redErrorButton = QPushButton("Red")
        redErrorButton.setStyleSheet("background-color: red")

        redErrorButton.clicked.connect(lambda: self.taskParent.defineErrorBox("red"))

        errorLayout.addWidget(redErrorButton)
        blueErrorButton = QPushButton("Blue")
        blueErrorButton.setStyleSheet("background-color: blue")

        blueErrorButton.clicked.connect(lambda: self.taskParent.defineErrorBox("blue"))

        errorLayout.addWidget(blueErrorButton)
        greenErrorButton = QPushButton("Green")
        greenErrorButton.setStyleSheet("background-color: green")

        greenErrorButton.clicked.connect(lambda: self.taskParent.defineErrorBox("green"))

        errorLayout.addWidget(greenErrorButton)
        root.addLayout(errorLayout)


        correctionLabel = QLabel("Correct Box")
        correctionLabel.setAlignment(Qt.AlignCenter)
        root.addWidget(correctionLabel)

        correctionLayout = QHBoxLayout(self)
        redCorrectionButton = QPushButton("Red Correction")
        redCorrectionButton.setStyleSheet("background-color: red")
        correctionLayout.addWidget(redCorrectionButton)

        redCorrectionButton.clicked.connect(lambda: self.taskParent.defineCorrectionBox("red"))

        blueCorrectionButton = QPushButton("Blue Correction")
        blueCorrectionButton.setStyleSheet("background-color: blue")
        correctionLayout.addWidget(blueCorrectionButton)

        blueCorrectionButton.clicked.connect(lambda: self.taskParent.defineCorrectionBox("blue"))

        greenCorrectionButton = QPushButton("Green Correction")
        greenCorrectionButton.setStyleSheet("background-color: green")

        greenCorrectionButton.clicked.connect(lambda: self.taskParent.defineCorrectionBox("green"))

        correctionLayout.addWidget(greenCorrectionButton)
        root.addLayout(correctionLayout)

    def startStuff(self, speed):
        self.animTimer.start(50)

        # Calculates the dist per step required to get to the halfway point for the arm
            # (Width / 2 ) / ( Total Steps )
                # (Width / 2) / (speed / timestep [50])
        self.distToHalfway = (self.sceneWidth /2 - self.boxHeight/2)  / (speed / 50)

    def renderNewBox(self, colour):

        match colour:
            case "red":
                boxCol = "#ff0000"
            case "green":
                boxCol = "#00ff00"
            case "blue":
                boxCol = "#0000ff"

        tempItem = QGraphicsRectItem(0, 0, self.boxHeight, self.boxHeight)
        tempItem.setY(self.conveyorTopLocation + self.conveyorHeight / 4)
        tempItem.setBrush(QBrush(QColor(boxCol)))
        tempItem.setZValue(500)
        self.boxArray.append(tempItem)
        self.scene.addItem(tempItem)

    def moveBox(self, disToMovePerMil):
        for box in self.boxArray:
            box.setX(box.x() + disToMovePerMil)

        # Changes state once the box at the front of the conveyor reaches the halfway point
        if(self.boxArray[0].x() >= self.sceneWidth /2 - self.boxHeight/2):
            if not self.interrupt:
                self.taskParent.advBoxQueue()
            else:
                self.animState = 2
                self.priorState = 1

    def doAnimationStep(self):
        match self.animState:
            case 0:
                self.moveBox(self.distToHalfway)
            case 1:
                self.moveToTarget()
            case 2:
                self.moveToTarget()

    def moveToTarget(self):
        if self.targetX == self.redX and self.heldBox.x() + self.addX > self.targetX:
            self.addX = self.targetX - self.heldBox.x() 
        elif self.targetX == self.blueX and self.heldBox.x() + self.addX < self.targetX:
            self.addX = self.targetX - self.heldBox.x() 

        
        if self.heldBox.y() - self.addY < self.targetY: 
            self.addY =  self.heldBox.y() - self.targetY
        

        # Sets the X/Y values to an incremement of their previous state
        self.heldBox.setX(self.heldBox.x() + self.addX)
        self.heldBox.setY(self.heldBox.y() - self.addY)


        #print("Current X: " + str(self.heldBox.x()) + ", Target X: " + str(self.targetX) + ", Add X: " + str(self.addX))
        #print("Current Y: " + str(self.heldBox.y()) + ", Target Y: " + str(self.targetY) + ", Add Y: " + str(self.addY))\
        print(self.heldBox.y() <= self.targetY and abs(self.heldBox.x()) >= self.targetX)
        print(self.targetX == self.blueX and self.heldBox.y() <= self.targetY and abs(self.heldBox.x()) <= self.targetX)
        
        if self.heldBox.y() <= self.targetY and abs(self.heldBox.x()) >= self.targetX or self.targetX == self.blueX and self.heldBox.y() <= self.targetY and abs(self.heldBox.x()) <= self.targetX:
           print("moveToTarget Completed.") 
            # If we are not in the interrupt state then move to state 0 
           if not self.interrupt:
               self.taskParent.createNewBox()
               self.boxArray.pop(0)
               self.taskParent.popBox()
               
            # If we are in the interrupt state and we have no recorded prior state (AKA, the interrupt hasn't finished)
           elif self.interrupt == True and self.priorState is not None:
               self.animState = 2
               self.correctBox(self.errorColour, self.correctedColour)
               self.priorState = 0

           # If we are in interrupt state and we have a recorded prior state, then clear the state 
           else:
               # Set state back
               if self.priorState == 1:
                   self.taskParent.advBoxQueue()
               elif self.priorState == 0:
                   self.taskParent.createNewBox()
               self.priorState = None
               self.interrupt = False


           # Remove boxes that are hidden or not needed
           if self.toDestroyBox is not None:
               self.scene.removeItem(self.toDestroyBox)
               self.toDestroyBox = None

    def correctBox(self, currentBox, newBox):
        # Probably better way to do this but w/e it's done only once so we can be slightly more inefficient
        match newBox:
            case "red":
                self.targetX = self.redX
                if self.redSB is not None:
                    self.toDestroyBox = self.redSB
                    #self.redSB = None
            case "green":
                self.targetX = self.greenX
                if self.greenSB is not None:
                    self.toDestroyBox = self.greenSB
                    #self.greenSB = None
            case "blue":
                self.targetX = self.blueX
                if self.blueSB is not None:
                    self.toDestroyBox = self.blueSB
                    #self.blueSB = None

        match currentBox:
            case "red":
                self.heldBox = self.redSB
            case "green":
                self.heldBox = self.greenSB
            case "blue":
                self.heldBox = self.blueSB



        # Mainly placeholder until I can bother to work on proper animations. Animation in this stuff is difficult so Functionality Over Form for now
        # AddY is 0 since we're moving from a box to box and theyre all on the same Y
        self.addX = int(((self.targetX - int(self.sceneWidth / 2 - self.boxHeight / 2))) / (self.speed / 50))
        self.addY = 0




    def checkSortBox(self, colour):
        match(colour):
            case "blue":
                self.targetX = self.blueX

                if self.blueSB is not None:
                    self.toDestroyBox = self.blueSB
                    self.blueSB = None

                self.blueSB = self.boxArray[0]
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
                
        
        self.heldBox = self.boxArray[0]
        self.addX = int(((self.targetX - int(self.sceneWidth / 2 - self.boxHeight / 2))) / (self.speed / 50))
        self.addY = int(((self.conveyorTopLocation + self.conveyorHeight / 4) - self.targetY)  / (self.speed / 50))

        print("Box X: " + str(self.heldBox.x()) + ", Box Y: " + str(self.heldBox.y()) + ", Target X: " + str(self.targetX) + ", Target Y: " + str(self.targetY))




