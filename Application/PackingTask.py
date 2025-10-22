import random, math

from PyQt5.QtCore import QTimer, QRect, Qt
from PyQt5.QtGui import QBrush, QColor, QPen, QRadialGradient
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QLabel, QPushButton, QGraphicsTextItem, QGraphicsEllipseItem

import pygame
import os 
import sys 

from Task import Task

class PackagingTask(Task):
    def __init__(self, errorRateVal, speed, itemCount, distractions,resolutionW,resolutionH):
        self._errorRate = errorRateVal
        self._speed = speed

        self.beeperEnabled = distractions[1]
        self.flashLightEnabled = distractions[0]

        self.boxList = []

        self.programState = 0
        self.previousState = 0

        # Sorting Task Specific
        self.error = 0
        self.itemCount = itemCount


        self.renderWindow = packagingTaskWindow(resolutionW,resolutionH,self, self.itemCount, self.flashLightEnabled)
        self.renderWindow.speed = self._speed

        # Plays a beep, cool right?
        if self.beeperEnabled:
            pygame.mixer.init()
            self.player = pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Sounds\\beep.wav"))
        
        if self.flashLightEnabled or self.beeperEnabled:
            self.distractionTimer = QTimer()
            self.distractionTimer.timeout.connect(self.doDistraction)


    # Commit exampole

    def createNewBox(self):
        self.renderWindow.animState = 0
        self.renderWindow.renderNewBox()

    def doDistraction(self):
        if random.uniform(0.0,1.0) > 0.75:
            if self.beeperEnabled:
                self.player.play()
            if self.flashLightEnabled:
                self.renderWindow.distractionFlash()
                QTimer.singleShot(500, self.renderWindow.distractionFlash)
                

    def advBoxQueue(self):
        # Checks for an error
        boxNum = self.itemCount
        if self.causeError():
            boxNum = boxNum + self.decideNegative()
        self.boxList.append(boxNum)

        self.renderWindow.animState = 1
            

    def startTask(self):

        for i in range(1):
            self.createNewBox()

        self.renderWindow.startStuff(self._speed)
        if self.distractionTimer is not None:
            self.distractionTimer.start(500)

    def decideNegative(self):
        if random.uniform(0.0,1.0) > 0.5:
            return 1
        else:   
            return -1

    def popBox(self):
        self.boxList.pop(0)

    def pause(self):
        self.renderWindow.animTimer.stop()
        if self.distractionTimer is not None:
            self.distractionTimer.stop()

    def resume(self):
        self.renderWindow.startStuff(self._speed)
        if self.distractionTimer is not None:
            self.distractionTimer.start(500)




    def causeError(self):
        # Does this work? Does this make sense, I'll never tell~
        error = self._errorRate + random.uniform(-0.05, 0.05) >= random.uniform(0.0,1.0)
        if error:
            return True
        else:
            return False


class packagingTaskWindow(QFrame):
    def __init__(self, minWidth, minHeight, taskParent, itemCount, flashLight):
        super().__init__()

        self.setObjectName("packagingTask")
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

        ##############
        ## Controls ##
        ##############
        errorLabel = QLabel("Count Error")
        errorLabel.setAlignment(Qt.AlignCenter)
        root.addWidget(errorLabel)

        errorLayout = QHBoxLayout(self)
        self.plusErrorButton = QPushButton("+")
        self.plusErrorButton.setStyleSheet("background-color: green")

        self.plusErrorButton.clicked.connect(lambda: self.correctBox("plus"))

        errorLayout.addWidget(self.plusErrorButton)
        self.minusErrorButton = QPushButton("-")
        self.minusErrorButton.setStyleSheet("background-color: red")

        self.minusErrorButton.clicked.connect(lambda: self.correctBox("minus"))

        errorLayout.addWidget(self.minusErrorButton)
        root.addLayout(errorLayout)


        # Anim State:
            # 0 = Move box along line
            # 1 = Move Arm to box position
            # 2 = Move Arm to appropriate box
            # 3 = General interrupt if needed
        self.animState = 0
        self.animTimer = QTimer()
        self.animTimer.timeout.connect(self.doAnimationStep)

        self.filledArray = []
        self.unfilledArray = []

        self.distToHalfway = 0
        self.priorState = None
        self.interrupt = False
        self.speed = None
        self.spawnTimer = 0


    def startStuff(self, speed):
        self.animTimer.start(50)

        # Calculates the dist per step required to get to the halfway point for the arm
            # (Width / 2 ) / ( Total Steps )
                # (Width / 2) / (speed / timestep [50])
        self.distToHalfway = (self.sceneWidth /2 - self.boxHeight/2)  / (speed / 50)
        self.speed = speed

    def distractionFlash(self):
        self.lightFlash.setVisible(not self.lightFlash.isVisible())                    
    
    def renderNewBox(self):
        tempItem = QGraphicsRectItem(0, 0, self.boxHeight, self.boxHeight)
        tempItem.setY(self.conveyorTopLocation + self.conveyorHeight / 4)
        tempItem.setBrush(QBrush(QColor("#fffe00")))
        tempItem.setZValue(500)
        self.unfilledArray.append(tempItem)
        self.scene.addItem(tempItem)

    def moveBox(self, disToMovePerMil):
        
        if random.uniform(0.0,1.0) > 0.4 + random.uniform(-0.1,0.1) and self.spawnTimer >= self.speed / 2: 
            self.spawnTimer = 0
            self.taskParent.createNewBox()
        else:
            self.spawnTimer += 50

        for box in self.unfilledArray:
            box.setX(box.x() + disToMovePerMil)
    
        for box in self.filledArray:
            box.setX(box.x() + disToMovePerMil)
            if box.x() > self.sceneWidth:
                self.scene.removeItem(box)
                self.filledArray.pop(0)
                self.taskParent.boxList.pop(0)

        # Panic create new box
        if len(self.unfilledArray) <= 0:
            print("?")
            self.taskParent.createNewBox()

        # Changes state once the box at the front of the conveyor reaches the halfway point
        if(self.unfilledArray[0].x() >= self.sceneWidth /2):
            
            if not self.interrupt:
                self.taskParent.advBoxQueue()
            else:
                self.animState = 2
                self.priorState = 1

    def removeItem(self, item):
        childArray = item.childItems()
        endIndex = len(childArray) - 1
        self.scene.removeItem(childArray[endIndex])

    def addItem(self, item):
        newChildNum  = len(item.childItems())
        self.addBox(item, newChildNum)
    

    def correctBox(self, action):
        index = 0
        for b in self.filledArray:
            print(self.taskParent.boxList[index])
            print(str(index))
            if action == "plus" and self.taskParent.boxList[index] < self.taskParent.itemCount:
                
                self.addItem(b)
                self.taskParent.error -= 1
                self.taskParent.boxList[index] += 1
            elif action == "minus" and self.taskParent.boxList[index] > self.taskParent.itemCount:
                self.removeItem(b)
                self.taskParent.error -= 1
                self.taskParent.boxList[index] -= 1
            index += 1
    
  

    def doAnimationStep(self):
        match self.animState:
            case 0:
                self.moveBox(self.distToHalfway)
            case 1: 
                self.fillBox()
  
    def addBox(self, item, position):
        insideBox = QGraphicsRectItem(0,0, self.boxHeight / 6, self.boxHeight / 6, item)
        insideBox.setPos(item.boundingRect().topLeft())
        insideBox.setX(insideBox.x() + ((position % 3)) * self.boxHeight / 3 + self.boxHeight/16)
        insideBox.setY(insideBox.y() + (math.floor(position/3)) * self.boxHeight / 3 + self.boxHeight/16)
    
    def fillBox(self):
        if len(self.unfilledArray[0].childItems()) == self.taskParent.boxList[len(self.taskParent.boxList) - 1]:
            self.filledArray.append(self.unfilledArray[0])
            self.unfilledArray.pop(0)
            
            self.animState = 0
        else: 
            self.addBox(self.unfilledArray[0], len(self.unfilledArray[0].childItems()))


        




