import random

from PyQt5.QtCore import QTimer, QRect, Qt
from PyQt5.QtGui import QBrush, QColor, QPen, QRadialGradient
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QLabel, QPushButton, QGraphicsTextItem, QGraphicsEllipseItem

import pygame
import os 
import sys 

from Task import Task

class SortingTask(Task):
    def __init__(self, errorRateVal, speed, numColours, distractions):
        self._errorRate = errorRateVal
        self._speed = speed
        self.numColours = numColours
        self.beeperEnabled = distractions[1]
        self.flashLightEnabled = distractions[0]

        self.boxList = []

        self.programState = 0
        self.previousState = 0

        # Sorting Task Specific
        self.error = 0

        self.errorBox = None
        self.correctBox = None


        self.renderWindow = sortingTaskWindow(640,1080,self, self.numColours, self.flashLightEnabled)
        self.renderWindow.speed = self._speed

        # Prevents the creation of a kill timer if one exists
        self.killTimerExists = False

        # Plays a beep, cool right?
        if self.beeperEnabled:
            pygame.mixer.init()
            self.player = pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Sounds\\beep.wav"))
        
        if self.flashLightEnabled or self.beeperEnabled:
            self.distractionTimer = QTimer()
            self.distractionTimer.timeout.connect(self.doDistraction)


    # Commit exampole

    def createNewBox(self):
        colour = self.getRandomColour()
        self.boxList.append(colour)
        self.renderWindow.animState = 0
        self.renderWindow.renderNewBox(colour)

    def doDistraction(self):
        if random.uniform(0.0,1.0) > 0.75:
            if self.beeperEnabled:
                self.player.play()
            if self.flashLightEnabled:
                self.renderWindow.distractionFlash()
                QTimer.singleShot(500, self.renderWindow.distractionFlash)
                






    def advBoxQueue(self):
        boxLocation = self.boxList[0]

        # Checks for an error
        if self.causeError():
            self.error += 1
            match self.boxList[0]:
                case "red":

                    if self.numColours == 3:
                        if random.uniform(0.0, 1.0) >= 0.5:
                            boxLocation = 'blue'
                        else:
                            boxLocation = 'green'
                    else:
                        boxLocation = 'blue'

                case "blue":
                    if self.numColours == 3:
                        if random.uniform(0.0, 1.0) >= 0.5:
                            boxLocation = 'red'
                        else:
                            boxLocation = 'green'
                    else:
                        boxLocation = 'red'

                case "green":
                    if random.uniform(0.0, 1.0) >= 0.5:
                        boxLocation = 'blue'
                    else:
                        boxLocation = 'red'



 

        self.renderWindow.checkSortBox(boxLocation, self.boxList[0])


        self.renderWindow.animState = 1

    def startTask(self):

        for i in range(1):
            self.createNewBox()

        self.renderWindow.startStuff(self._speed)
        if self.distractionTimer is not None:
            self.distractionTimer.start(500)


    def popBox(self):
        self.boxList.pop(0)


    def getRandomColour(self):

        if self.numColours == 3:
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
        self.renderWindow.defineLabel("error", boxColour.title(), boxColour)

        if self.correctBox is not None:
            self.correctionInterrupt()

    def defineCorrectionBox(self, boxColour):
        self.correctBox = boxColour
        self.renderWindow.defineLabel("corrected", boxColour.title(), boxColour)

        if self.errorBox is not None:
            self.correctionInterrupt()

    def correctionInterrupt(self):
        if self.correctBox == self.errorBox: 
            # Error or beep will go here. 
            self.cleanInterruptValues()
            self.renderWindow.defineLabel("warning","A box is not correctly sorted if it is in it's appropriate coloured box. Selections annulled")
            # Timer that kills itself after a second
            if not self.killTimerExists:
                QTimer.singleShot(1500, self.cleanWarning)
                self.killTimerExists = True
            return

        if not self.renderWindow.interrupt:
            self.renderWindow.errorColour = self.errorBox
            self.renderWindow.correctedColour = self.correctBox
            self.renderWindow.interrupt = True
    
    def cleanInterruptValues(self):
        self.errorBox = None
        self.correctBox = None
        self.renderWindow.defineLabel("error", "", "black")
        self.renderWindow.defineLabel("corrected", "", "black")
        
    def cleanWarning(self):
        self.renderWindow.defineLabel("warning", "")
        self.killTimerExists = False


    def causeError(self):
        # Does this work? Does this make sense, I'll never tell~
        error = self._errorRate + random.uniform(-0.05, 0.05) >= random.uniform(0.0,1.0)
        if error:
            return True
        else:
            return False


class sortingTaskWindow(QFrame):
    def __init__(self, minWidth, minHeight, taskParent, numColours, flashLight):
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

        self.numColours = numColours

        ####################
        ## Flashing Light ##
        ####################
        if flashLight:
            lightSize = ((self.minHeight / 2) / 4) / 2
            self.lightFlash = QGraphicsEllipseItem(0,0, lightSize * 0.5, lightSize * 0.5)
            self.lightFlash.setBrush(QBrush(QColor(255,234,0)))
            self.lightFlash.setX( self.sceneWidth - self.sceneWidth / 16)
            self.lightFlash.setY(self.sceneHeight / 16)
            self.scene.addItem(self.lightFlash)
            self.lightFlash.setVisible(False)


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
        self.blueSBCol = None
        self.greenSB = None
        self.greenSBCol = None
        self.redSB = None
        self.redSBCol = None
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
        selectedItemLayout = QHBoxLayout(self)
        self.errorBoxSelected = QLabel("Box with Error: ")
        self.errorBoxSelected.setStyleSheet("font-weight: bold")
        self.errorBoxSelected.setAlignment(Qt.AlignCenter)
        self.correctBoxSelected = QLabel("Correct Box: ")
        self.correctBoxSelected.setStyleSheet("font-weight: bold")
        self.correctBoxSelected.setAlignment(Qt.AlignCenter)
        self.warningBox = QLabel("")
        self.warningBox.setStyleSheet("font-weight: bold; color: red")
        self.warningBox.setAlignment(Qt.AlignCenter)
        selectedItemLayout.addWidget(self.errorBoxSelected)
        selectedItemLayout.addWidget(self.warningBox)
        selectedItemLayout.addWidget(self.correctBoxSelected)
        root.addLayout(selectedItemLayout)

        

        errorLabel = QLabel("Box With Error")
        errorLabel.setAlignment(Qt.AlignCenter)
        root.addWidget(errorLabel)

        errorLayout = QHBoxLayout(self)
        self.redErrorButton = QPushButton("Red")
        self.redErrorButton.setStyleSheet("background-color: red")

        self.redErrorButton.clicked.connect(lambda: self.taskParent.defineErrorBox("red"))

        errorLayout.addWidget(self.redErrorButton)
        self.blueErrorButton = QPushButton("Blue")
        self.blueErrorButton.setStyleSheet("background-color: blue")

        self.blueErrorButton.clicked.connect(lambda: self.taskParent.defineErrorBox("blue"))

        errorLayout.addWidget(self.blueErrorButton)

        if numColours == 3:
            self.greenErrorButton = QPushButton("Green")
            self.greenErrorButton.setStyleSheet("background-color: green")

            self.greenErrorButton.clicked.connect(lambda: self.taskParent.defineErrorBox("green"))
            errorLayout.addWidget(self.greenErrorButton)

        root.addLayout(errorLayout)


        correctionLabel = QLabel("Correct Box")
        correctionLabel.setAlignment(Qt.AlignCenter)
        root.addWidget(correctionLabel)

        correctionLayout = QHBoxLayout(self)
        self.redCorrectionButton = QPushButton("Red Correction")
        self.redCorrectionButton.setStyleSheet("background-color: red")
        correctionLayout.addWidget(self.redCorrectionButton)

        self.redCorrectionButton.clicked.connect(lambda: self.taskParent.defineCorrectionBox("red"))

        self.blueCorrectionButton = QPushButton("Blue Correction")
        self.blueCorrectionButton.setStyleSheet("background-color: blue")
        correctionLayout.addWidget(self.blueCorrectionButton)

        self.blueCorrectionButton.clicked.connect(lambda: self.taskParent.defineCorrectionBox("blue"))
        
        if numColours == 3:
            self.greenCorrectionButton = QPushButton("Green Correction")
            self.greenCorrectionButton.setStyleSheet("background-color: green")

            self.greenCorrectionButton.clicked.connect(lambda: self.taskParent.defineCorrectionBox("green"))
            correctionLayout.addWidget(self.greenCorrectionButton)

        root.addLayout(correctionLayout)

    def startStuff(self, speed):
        self.animTimer.start(50)

        # Calculates the dist per step required to get to the halfway point for the arm
            # (Width / 2 ) / ( Total Steps )
                # (Width / 2) / (speed / timestep [50])
        self.distToHalfway = (self.sceneWidth /2 - self.boxHeight/2)  / (speed / 50)

    def defineLabel(self, label, text, newColour = None):
        match label:
            case "error":
                self.errorBoxSelected.setText("Box with Error: " + text)
                if newColour is not None:
                    self.errorBoxSelected.setStyleSheet("font-weight: bold; color: " + newColour)
            case "corrected":
                self.correctBoxSelected.setText("Correct Box: " + text)
                if newColour is not None:
                    self.correctBoxSelected.setStyleSheet("font-weight: bold; color: " + newColour)
            case "warning":
                self.warningBox.setText(text)

    def distractionFlash(self):
        self.lightFlash.setVisible(not self.lightFlash.isVisible())                    
    
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
                self.correctBox(self.errorColour, self.correctedColour)

    def doAnimationStep(self):
        match self.animState:
            case 0:
                self.moveBox(self.distToHalfway)
            case 1:
                self.moveToTarget()
            case 2:
                self.animCorrectBox()

    def setButtonState(self, enabled):
        
        self.blueErrorButton.setEnabled(enabled)
        self.blueCorrectionButton.setEnabled(enabled)

        self.redErrorButton.setEnabled(enabled)
        self.redCorrectionButton.setEnabled(enabled)

        if self.numColours == 3:
            self.greenCorrectionButton.setEnabled(enabled)
            self.greenErrorButton.setEnabled(enabled)

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
           elif self.interrupt == True:
               self.animState = 2
               self.correctBox(self.errorColour, self.correctedColour)
               self.priorState = 0
               self.boxArray.pop(0)
               self.taskParent.popBox()

           # Remove boxes that are hidden or not needed
           if self.toDestroyBox is not None:
               self.scene.removeItem(self.toDestroyBox)
               self.toDestroyBox = None

    def animCorrectBox(self):
        print("We are in Anim CorrectBox. Target X: " + str(self.targetX) + ". Current X: " + str(self.heldBox.x()) + ". ErrorColour and correctedColour: " + str(self.errorColour) + " " + str(self.correctedColour) )
        print("addX: " + str(self.addX))

        if self.errorColour is None or self.correctedColour is None:
            self.cleanInterruptState()
            return

        # Encountered some issue with setting and equalting the position of certain box combos, this is a quick fix for this
        # I'm dead sure its a floating point issue which its why its called that, but if it isnt ah hehe hoho 
        floatingPointErrorSolve = False

        if self.targetX == self.redX and self.heldBox.x() + self.addX > self.targetX or self.targetX == self.greenX and self.errorColour == "blue" and self.heldBox.x() + self.addX > self.targetX:
            self.addX = self.targetX - self.heldBox.x() 
        elif self.targetX == self.blueX and self.heldBox.x() + self.addX < self.targetX or self.targetX == self.greenX and self.errorColour == "red" and self.heldBox.x() + self.addX < self.targetX:
            self.addX = self.targetX - self.heldBox.x() 

        if int(self.targetX) == int(self.heldBox.x()):
            floatingPointErrorSolve = True
            self.heldBox.setX(self.targetX)
            self.addX = 0

        self.heldBox.setX(self.heldBox.x() + self.addX)

        if self.heldBox.x() == self.targetX or floatingPointErrorSolve: 
            if self.priorState == 1:
                self.taskParent.advBoxQueue()
            elif self.priorState == 0:
                self.taskParent.createNewBox()
            
            self.priorState = None
            self.interrupt = False

            self.errorColour = None
            self.correctColour = None
            self.taskParent.cleanInterruptValues()
            self.taskParent.error -= 1

            self.setButtonState(True)

    def cleanInterruptState(self):
        if self.priorState == 1:
                self.taskParent.advBoxQueue()
        elif self.priorState == 0:
                self.taskParent.createNewBox()

        self.priorState = None
        self.interrupt = False

        self.errorColour = None
        self.correctColour = None
        self.taskParent.cleanInterruptValues()
        
        

    def correctBox(self, currentBox, newBox):
        # Probably better way to do this but w/e it's done only once so we can be slightly more inefficient
        if self.errorColour is None or self.correctedColour is None:
            self.cleanInterruptState()
            return
        
        match currentBox:
            case "red":
                # If currentBox already has the actual right colour in it (E.G red box in red box). Stop everything and give warning
                if currentBox == self.redSBCol:
                    self.defineLabel("warning", "No Error present in red box. This can occur if the box is in the process of being replaced by a new box")
                    self.cleanInterruptState()
                    return
                if newBox != self.redSBCol:
                    self.defineLabel("warning", "Cannot create an error. This error can also occur if the box is in the process of being replaced by a new box.")
                    self.cleanInterruptState()
                    return

                self.heldBox = self.redSB
                self.redSB = None
            case "green":
                if currentBox == self.greenSBCol:
                    self.defineLabel("warning", "No Error present in green box. This can occur if the box is in the process of being replaced by a new box")
                    self.cleanInterruptState()
                    return
                if newBox != self.greenSBCol:
                    self.defineLabel("warning", "Cannot create an error. This error can also occur if the box is in the process of being replaced by a new box.")
                    self.cleanInterruptState()
                    return
                self.heldBox = self.greenSB
                self.greenSB = None
            case "blue":
                if currentBox == self.blueSBCol:
                    self.defineLabel("warning", "No Error present in blue box. This can occur if the box is in the process of being replaced by a new box")
                    self.cleanInterruptState()
                    return
                if newBox != self.blueSBCol:
                    self.defineLabel("warning", "Cannot create an error. This error can also occur if the box is in the process of being replaced by a new box.")
                    self.cleanInterruptState()
                    return
                self.heldBox = self.blueSB
                self.blueSB =  None
        
        match newBox:
            case "red":
                self.targetX = self.redX
                if self.redSB is not None:
                    self.toDestroyBox = self.redSB
                self.redSB = self.heldBox
            case "green":
                self.targetX = self.greenX
                if self.greenSB is not None:
                    self.toDestroyBox = self.greenSB
                self.greenSB = self.heldBox
            case "blue":
                self.targetX = self.blueX
                if self.blueSB is not None:
                    self.toDestroyBox = self.blueSB
                self.blueSB = self.heldBox



        # If stuff gets here, we have no errors, so we can disable buttons
        self.setButtonState(False)

        # Mainly placeholder until I can bother to work on proper animations. Animation in this stuff is difficult so Functionality Over Form for now
        # AddY is 0 since we're moving from a box to box and theyre all on the same Y
        self.addX = int(((self.targetX - self.heldBox.x())) / (self.speed / 50))
        self.addY = 0




    def checkSortBox(self, colour, boxRealColour):
        match(colour):
            case "blue":
                self.targetX = self.blueX

                if self.blueSB is not None:
                    self.toDestroyBox = self.blueSB
                    self.blueSB = None

                self.blueSB = self.boxArray[0]
                self.blueSBCol = boxRealColour

            case "red":
                self.targetX = self.redX 

                if self.redSB is not None:
                    self.toDestroyBox = self.redSB
                    self.redSB = None

                self.redSB = self.boxArray[0]
                self.redSBCol = boxRealColour 

            case "green":
                self.targetX = self.greenX

                if self.greenSB is not None:
                    self.toDestroyBox = self.greenSB
                    self.greenSB = None

                self.greenSB = self.boxArray[0]
                self.greenSBCol = boxRealColour
                
        
        self.heldBox = self.boxArray[0]
        self.addX = int(((self.targetX - int(self.sceneWidth / 2 - self.boxHeight / 2))) / (self.speed / 50))
        self.addY = int(((self.conveyorTopLocation + self.conveyorHeight / 4) - self.targetY)  / (self.speed / 50))

        print("Box X: " + str(self.heldBox.x()) + ", Box Y: " + str(self.heldBox.y()) + ", Target X: " + str(self.targetX) + ", Target Y: " + str(self.targetY))




