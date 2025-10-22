import random

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QPushButton, QGraphicsTextItem, QLabel

from Task import Task

import pygame
import os
import sys

# -----------------------------------
# TASK CLASS
# -----------------------------------
class inspectionTask(Task):
    def __init__(self, errorRateVal, speed, acceptedRange, distractions, resolutionW, resolutionH):
        self._errorRate = errorRateVal
        self._speed = speed
        self._acceptedRange = acceptedRange

        self.itemList = []
        
        self.beeperEnabled = distractions[0]
        self.flashLightEnabled = distractions[1]

        self.correctCount = 0
        self.defectsMissed = 0
        self.totalInspected = 0

        self.programState = 0
        self.previousState = 0

        self.renderWindow = inspectionTaskWindow(resolutionW, resolutionH, self, self.flashLightEnabled)

        # Plays a beep, cool right?
        if self.beeperEnabled:
            pygame.mixer.init()
            self.player = pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Sounds\\beep.wav"))
        
        if self.flashLightEnabled or self.beeperEnabled:
            self.distractionTimer = QTimer()
            self.distractionTimer.timeout.connect(self.doDistraction)

    # -------------------------------
    # Properties
    # -------------------------------
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


    #--------------------------------
    # Distraction Logic
    #--------------------------------
    def doDistraction(self):
        if random.uniform(0.0,1.0) > 0.75:
            if self.beeperEnabled:
                self.player.play()
            if self.flashLightEnabled:
                self.renderWindow.distractionFlash()
                QTimer.singleShot(500, self.renderWindow.distractionFlash)

    # -------------------------------
    # Core Logic
    # -------------------------------
    def createNewBox(self):
        self.createNewItem()

    def advBoxQueue(self):
        pass

    def createNewItem(self):
        size = random.uniform(6.0, 14.0)
        self.itemList.append(size)
        self.renderWindow.renderNewItem(size)

    def evaluateItem(self, size):
        return 8.0 <= size <= self._acceptedRange

    def pause(self):
        self.renderWindow.animTimer.stop()
        if self.distractionTimer is not None:
            self.distractionTimer.stop()
    
    def resume(self):
        self.renderWindow.startStuff(self._speed)
        if self.distractionTimer is not None:
            self.distractionTimer.start(500)

    def performInspection(self):
        if not self.itemList:
            return

        # Evaluate the first item
        actual_size = self.itemList[0]
        true_result = self.evaluateItem(actual_size) 

        # Determine if a random error occurred
        error_happened = self.causeError()

        # Simulate measured result
        if error_happened:
            measured_result = not true_result
        else:
            measured_result = true_result

        # Update metrics
        self.totalInspected += 1

        # Count as correct only when measured matches true
        if not error_happened:
            self.correctCount += 1

        # Increment whenever a defect is missed.
        if error_happened:
            self.defectsMissed += 1

        # Update UI
        self.renderWindow.displayInspectionResult(true_result, measured_result)
        self.renderWindow.updateStatsLabel()

        # Remove inspected item from queue
        self.popItem()



    def startTask(self):
        # Create first item and start the conveyor
        self.createNewItem()
        self.renderWindow.startStuff(self._speed)
        if self.distractionTimer is not None:
            self.distractionTimer.start(500)




    def popItem(self):
        if self.itemList:
            self.itemList.pop(0)


    def causeError(self):
        error = self._errorRate + random.uniform(-0.05, 0.05) >= random.uniform(0.0, 1.0)
        return error


    def overrideResult(self, item):
        # Called when the user clicks a box to manually flip its pass/fail result.
        # Green = pass, Red = fail
    
        # Get current color of the box
        current_color = item.brush().color()

        if current_color == QColor(0, 255, 0):  # green = currently pass
            # Flip to fail
            item.setBrush(QBrush(QColor(255, 0, 0)))

            # Update metrics
            if self.correctCount > 0:
                self.correctCount -= 1
            self.defectsMissed += 1

        elif current_color == QColor(255, 0, 0):  # red = currently fail
            # Flip to pass
            item.setBrush(QBrush(QColor(0, 255, 0)))

            # Update metrics
            if self.defectsMissed > 0:
                self.defectsMissed -= 1
            self.correctCount += 1

        # Refresh stats
        self.renderWindow.updateStatsLabel()

        # Remove the item from the scene after 0.5 seconds
        QTimer.singleShot(500, lambda: item.scene().removeItem(item) if item.scene() else None)




















# -----------------------------------
# GUI CLASS
# -----------------------------------
class inspectionTaskWindow(QFrame):
    def __init__(self, minWidth, minHeight, taskParent, flashLight):
        super().__init__()

        self.setWindowTitle("Inspection Task Simulation")

        self.taskParent = taskParent
        self.sceneWidth = minWidth
        self.sceneHeight = int(minHeight/2)

        self.setObjectName("packagingTask")
        self.setStyleSheet("""QFrame { border: 1px solid #d0d0d0; border-radius: 5px; background: #fafafa;}
        QLabel { font-size: 4vmin;}
        QPushButton { padding: 4px 8px;}""")

        self.setMinimumSize(minWidth, minHeight)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Scene setup
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.sceneWidth, self.sceneHeight)
        self.scene.setBackgroundBrush(QBrush(QColor(105, 105, 105)))

        # Conveyor setup
        self.conveyorHeight = int(self.sceneHeight / 4)
        self.conveyorTopLocation = int(self.sceneHeight / 2 + self.sceneHeight / 6)
        conveyor = QGraphicsRectItem(0, self.conveyorTopLocation, self.sceneWidth, self.conveyorHeight)
        conveyor.setBrush(QBrush(QColor(155, 155, 155)))
        conveyor.setZValue(1)
        self.scene.addItem(conveyor)

        # Viewport
        viewport = QGraphicsView(self.scene)
        viewport.setInteractive(False)
        viewport.setFixedSize(self.sceneWidth, self.sceneHeight)
        viewport.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        viewport.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12,12,12,12)
        layout.setSpacing(8)
        layout.addWidget(viewport)

        #stats labels
        self.statsLabel = QLabel("Inspected: 0  |  Passed: 0  |  Failed: 0")
        self.statsLabel.setStyleSheet("color: black; font-size: 18px; font-weight: bold;")
        self.statsLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.statsLabel)

        # Controls
        selectedItemLayout = QHBoxLayout(self)

        self.warningBox = QLabel("")
        self.warningBox.setStyleSheet("font-weight: bold; color: red")
        self.warningBox.setAlignment(Qt.AlignCenter)
        selectedItemLayout.addWidget(self.warningBox)
        layout.addLayout(selectedItemLayout)
        

        

        errorLabel = QLabel("Bin With Error")
        errorLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(errorLabel)

        errorLayout = QHBoxLayout(self)
        self.acceptedErrorButton = QPushButton("Accepted")
        self.acceptedErrorButton.setStyleSheet("background-color: green")

        self.acceptedErrorButton.clicked.connect(lambda: self.correctItem("accepted"))

        errorLayout.addWidget(self.acceptedErrorButton)
        self.rejectedErrorButton = QPushButton("Rejected")
        self.rejectedErrorButton.setStyleSheet("background-color: red")

        self.rejectedErrorButton.clicked.connect(lambda: self.correctItem("rejected"))

        errorLayout.addWidget(self.rejectedErrorButton)

        layout.addLayout(errorLayout)

        # Animation setup
        self.conveyorItems = []     # Items moving along conveyor
        self.animatedItems = []     # Items moving to bins
        self.animTimer = QTimer()
        self.animTimer.timeout.connect(self.doAnimationStep)
        self.animState = 0
        self.priorState = 0
        

        # Pass/fail bin locations
        self.passBinX, self.passBinY = 50, 50
        self.failBinX, self.failBinY = self.sceneWidth - 150, 50

        # Box location
        self.rejectedBox = []
        self.acceptedBox = []
        self.correctingBox = None
        
        # Box Spawning 
        self.spawnTimer = 0

        # Flashing Light
        
        ####################
        ## Flashing Light ##
        ####################
        if flashLight:
            lightSize = ((minHeight / 2) / 4) / 2
            self.lightFlash = QGraphicsEllipseItem(0,0, lightSize * 0.5, lightSize * 0.5)
            self.lightFlash.setBrush(QBrush(QColor(255,234,0)))
            self.lightFlash.setX( self.sceneWidth - self.sceneWidth / 16)
            self.lightFlash.setY(self.sceneHeight / 16)
            self.scene.addItem(self.lightFlash)
            self.lightFlash.setVisible(False)


        # Animation parameters
        self.speed = 0  # default, will be updated by task speed
        self.pixelPerFrame = 2
        self.currentItem = None

    def distractionFlash(self):
        self.lightFlash.setVisible(not self.lightFlash.isVisible())   


    def startStuff(self, speed):
        self.speed = speed
        #self.pixelPerFrame = max(1, int(speed * 0.25))  # slower = smoother
        self.pixelPerFrame = int(((self.sceneWidth/2))  / (speed / 50))
        self.animTimer.start(50)

    def renderNewItem(self, size):
        # Compute box size
        boxWidth = int((size / 15.0) * 100) + 20
        y = self.conveyorTopLocation + self.conveyorHeight / 4

        item = QGraphicsRectItem(0,0,boxWidth, 30)

        item.setBrush(QBrush(QColor(200, 200, 200)))
        item.setZValue(500)
        item.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.scene.addItem(item)

        item.setPos(0, y)

        # Create text
        text = QGraphicsTextItem(f"{size:.1f}", item)
        text.setDefaultTextColor(QColor(0, 0, 0))
        text.setZValue(600)

        # Center text inside box (local coords)
        text_rect = text.boundingRect()
        box_rect = item.rect()
        text.setPos(
            (box_rect.width() - text_rect.width()) / 2,
            (box_rect.height() - text_rect.height()) / 2
        )
        item.textItem = text

        # Add to conveyor
        self.conveyorItems.append(item)



    def moveConveyorItems(self):
        """Move all items along the conveyor and inspect if they reach middle"""
        items_to_inspect = []

        if random.uniform(0.0, 1.0) > 0.4 + random.uniform(-0.5, 0.5) and self.spawnTimer >= self.speed / 2:
            self.taskParent.createNewItem()
            self.spawnTimer = 0
        else:
            self.spawnTimer += 50

        for item in self.conveyorItems:
            item.setX(item.x() + self.pixelPerFrame)

            if item.x() >= self.sceneWidth / 2:
                items_to_inspect.append(item)
                self.animState = 1
                
        

        for item in items_to_inspect:
            self.conveyorItems.remove(item)
            self.currentItem = item
            self.taskParent.performInspection()  # sets color and target

    def displayInspectionResult(self, intendedResult, result):
        """Color-code inspected item and set target bin for animation"""
        if self.currentItem is None:
            return

        if intendedResult:
            self.currentItem.setBrush(QBrush(QColor(0, 255, 0)))
        else:
            self.currentItem.setBrush(QBrush(QColor(255, 0, 0)))


        if result:
            targetX, targetY = self.passBinX, self.passBinY
        else:
            targetX, targetY = self.failBinX, self.failBinY

        # Animate to bin
        steps = self.speed / 100 # slower speed = more steps

        self.animatedItems.append({
            "item": self.currentItem,
            "error": not (intendedResult == result),
            "result": result,
            "targetX": targetX,
            "targetY": targetY,
            "steps": steps,
            "currentStep": 0
        })

        self.updateStatsLabel()

        self.currentItem = None  # reset for next item

    def correctItem(self, incorrectBox):

        

        if incorrectBox == "accepted":
            if len(self.acceptedBox) <= 0:
                return

            box = self.acceptedBox[0]
            targetX, targetY = self.failBinX, self.failBinY
        else:
            if len(self.rejectedBox)  <= 0:
                return
            box = self.rejectedBox[0]
            targetX, targetY = self.passBinX, self.passBinY 

        refBox = box["item"]

        if not box["error"]:
            print("NO ERROR")
            return
            

        steps = self.speed / 100


        self.correctingBox = {
            "item": refBox,
            "error": False,
            "result": False,
            "targetX": targetX,
            "targetY": targetY,
            "steps": steps,
            "currentStep": 0
        }
        self.priorState = self.animState
        self.animState = 2
    
    def moveToTarget(self, box, mode):
                # Animate items moving to bins
        data = box

        item = data["item"]
        steps = data["steps"]
        data["currentStep"] += 1
            
           
        if data["currentStep"] >= steps:
            # Finalize position at bin
            item.setX(data["targetX"])
            item.setY(data["targetY"])
            if mode == "inspect":
                self.animatedItems.remove(data)
                self.animState = 0
            elif mode == "correct":
                self.taskParent.defectsMissed -= 1
                self.animState = self.priorState
            


                # Adds box to the appropriate pile, and removes the box beneath it
            if data["result"]:
                self.acceptedBox.append({
                    "item":item,
                    "error": data["error"]
                })

                if len(self.acceptedBox) > 1:
                    oldItem = self.acceptedBox[0]
                    self.removeItemFromScene(oldItem["item"])
                    self.acceptedBox.pop(0)

            else:
                self.rejectedBox.append({
                    "item":item,
                    "error": data["error"]
                })
                if len(self.rejectedBox) > 1:
                    oldItem = self.rejectedBox[0]
                    self.removeItemFromScene(oldItem["item"])
                    self.rejectedBox.pop(0)

        else:
            dx = (data["targetX"] - item.x()) / (steps - data["currentStep"] + 1)
            dy = (data["targetY"] - item.y()) / (steps - data["currentStep"] + 1)
            item.setX(item.x() + dx)
            item.setY(item.y() + dy)

    def doAnimationStep(self):
        """Move conveyor and animate items toward bins"""
        # Move conveyor items
        print("We are actively in doAnimStep, current animState is: " + str(self.animState))
        match self.animState:
            case 0:
                self.moveConveyorItems()
            case 1:
                self.moveToTarget(self.animatedItems[0], "inspect")
            case 2:
                self.moveToTarget(self.correctingBox, "correct")

    #updates the metrics lables with the correct stats
    def updateStatsLabel(self):
        """Refresh the on-screen stats"""
        inspected = self.taskParent.totalInspected
        passed = self.taskParent.correctCount
        failed = self.taskParent.defectsMissed
        self.statsLabel.setText(f"Inspected: {inspected}  |  Passed: {passed}  |  Failed: {failed}")

    #removes item from the scene after the 5 seconds QTimer in doAnimationStep
    def removeItemFromScene(self, item):
        """Safely remove an item from the scene."""
        if item.scene() is not None:
            self.scene.removeItem(item)


        
