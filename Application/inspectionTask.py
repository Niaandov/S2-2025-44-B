"""
Updates:
- Made it so that items range from 6cm to 14cm, meaning items outside of 8cm-12cm will auto fail
- Added labels inside each item so that there is a visual queue of how big the item actually is
- Added a pause/resume button
- Added performacne stats on screen updating in real time
- Added user input. If the user clicks on a box it will reverse the metrics decision 
        flash yellow and then be removed from the scene.
- made it so boxes are removed after 5 seconds from being classified to save on system memory.
"""



import random

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QPushButton, QGraphicsTextItem, QLabel

from Task import Task

# -----------------------------------
# TASK CLASS
# -----------------------------------
class inspectionTask(Task):
    def __init__(self, errorRateVal, speed, acceptedRange):
        self._errorRate = errorRateVal
        self._speed = speed
        self._acceptedRange = acceptedRange

        self.itemList = []

        self.correctCount = 0
        self.defectsMissed = 0
        self.totalInspected = 0

        self.programState = 0
        self.previousState = 0

        self.renderWindow = inspectionTaskWindow(1920, 1080, self)

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
    def __init__(self, minWidth, minHeight, taskParent):
        super().__init__()

        self.setWindowTitle("Inspection Task Simulation")

        self.taskParent = taskParent
        self.sceneWidth = minWidth
        self.sceneHeight = int(minHeight / 2)

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
        viewport.setInteractive(True)
        viewport.setFixedSize(self.sceneWidth, self.sceneHeight)
        viewport.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        viewport.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout = QVBoxLayout(self)
        layout.addWidget(viewport)

        #start button
        self.startButton = QPushButton("Start Simulation")
        layout.addWidget(self.startButton)

        self.startButton.clicked.connect(self.onStartClicked)

        #pause/resume button
        self.pauseButton = QPushButton("Pause/Resume Simulation")
        layout.addWidget(self.pauseButton)

        self.pauseButton.clicked.connect(self.onPauseClicked)
        self.pauseButton.setEnabled(False)
        

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


        # Animation parameters
        self.speed = 0  # default, will be updated by task speed
        self.pixelPerFrame = 2
        self.currentItem = None

    #function for the start button
    def onStartClicked(self):
        self.taskParent.startTask()
        self.startButton.setEnabled(False)
        self.pauseButton.setEnabled(True)
        self.animTimer.start(50)

    #function for the pause button
    def onPauseClicked(self):
        """Toggle pause/resume for the simulation"""
        if hasattr(self, "paused") and self.paused:
            # Resume simulation
            self.animTimer.start(50)
            self.pauseButton.setText("Pause Simulation")
            self.paused = False
        else:
            # Pause simulation
            self.animTimer.stop()
            if hasattr(self.taskParent, "itemTimer"):
                self.taskParent.itemTimer.stop()
            self.pauseButton.setText("Resume Simulation")
            self.paused = True



    def startStuff(self, speed):
        self.speed = speed
        #self.pixelPerFrame = max(1, int(speed * 0.25))  # slower = smoother
        self.pixelPerFrame = int(((self.sceneWidth/2))  / (speed / 50))

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

        if random.uniform(0.0, 1.0) > 0.4 + random.uniform(-0.5, 0.5) and self.spawnTimer >= 500:
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


        
