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
from PyQt5.QtWidgets import QVBoxLayout, QFrame, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QPushButton, QGraphicsTextItem, QLabel

from Task import Task

# -----------------------------------
# TASK CLASS
# -----------------------------------
class inspectionTask(Task):
    def __init__(self, errorRateVal, speed):
        self._errorRate = errorRateVal
        self._speed = speed

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
        return 8.0 <= size <= 12.0

    def performInspection(self):
        if not self.itemList:
            return

        # Evaluate the first item
        actual_size = self.itemList[0]
        true_result = self.evaluateItem(actual_size)  # True = within spec, False = defective

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
        if measured_result == true_result:
            self.correctCount += 1

        # Increment defectsMissed when actual item is defective OR when a random error occurred
        if (not true_result) or error_happened:
            self.defectsMissed += 1

        # Update UI
        self.renderWindow.displayInspectionResult(actual_size, measured_result)
        self.renderWindow.updateStatsLabel()

        # Remove inspected item from queue
        self.popItem()



    def startTask(self):
        # Create first item and start the conveyor
        self.createNewItem()
        self.renderWindow.startStuff(self._speed)


        self.itemTimer = QTimer()
        self.itemTimer.timeout.connect(self.createNewItem)

        self.itemTimer.start(int(1000)) #this will spawn a new Item every 1 second

        # self.itemTimer.start(int(self._speed * 100)) # played around with making the spawning speed tied to the speed varible 
                                                            # but could never get it working right. introduced bugs where it 
                                                            # would only spawn one item and then stop.



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


        # Animation setup
        self.conveyorItems = []     # Items moving along conveyor
        self.animatedItems = []     # Items moving to bins
        self.animTimer = QTimer()
        self.animTimer.timeout.connect(self.doAnimationStep)
        self.animTimer.start(50)

        # Pass/fail bin locations
        self.passBinX, self.passBinY = 50, 50
        self.failBinX, self.failBinY = self.sceneWidth - 150, 50




        # Animation parameters
        self.speed = 0  # default, will be updated by task speed
        self.pixelPerFrame = 2
        self.currentItem = None

    #function for the start button
    def onStartClicked(self):
        self.taskParent.startTask()
        self.startButton.setEnabled(False)
        self.pauseButton.setEnabled(True)

    #function for the pause button
    def onPauseClicked(self):
        """Toggle pause/resume for the simulation"""
        if hasattr(self, "paused") and self.paused:
            # Resume simulation
            self.animTimer.start(50)
            if hasattr(self.taskParent, "itemTimer"):
                self.taskParent.itemTimer.start(int(1000))
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
        self.pixelPerFrame = max(1, int(speed * 0.25))  # slower = smoother

    def renderNewItem(self, size):
        # Compute box size
        boxWidth = int((size / 15.0) * 100) + 20
        y = self.conveyorTopLocation + self.conveyorHeight / 4

        # i create the rectanges using the clickableBox class so that I can make them interactive
        item = ClickableBox(boxWidth, 30, size, self.taskParent)

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
        for item in self.conveyorItems:
            item.setX(item.x() + self.pixelPerFrame)


            if item.x() >= self.sceneWidth / 2:
                items_to_inspect.append(item)

        for item in items_to_inspect:
            self.conveyorItems.remove(item)
            self.currentItem = item
            self.taskParent.performInspection()  # sets color and target

    def displayInspectionResult(self, size, result):
        """Color-code inspected item and set target bin for animation"""
        if self.currentItem is None:
            return

        if result:
            self.currentItem.setBrush(QBrush(QColor(0, 255, 0)))
            targetX, targetY = self.passBinX, self.passBinY
        else:
            self.currentItem.setBrush(QBrush(QColor(255, 0, 0)))
            targetX, targetY = self.failBinX, self.failBinY

        # Animate to bin
        steps = max(10, int(100 / self.speed))  # slower speed = more steps
        self.animatedItems.append({
            "item": self.currentItem,
            "targetX": targetX,
            "targetY": targetY,
            "steps": steps,
            "currentStep": 0
        })

        self.updateStatsLabel()

        self.currentItem = None  # reset for next item
        

    def doAnimationStep(self):
        """Move conveyor and animate items toward bins"""
        # Move conveyor items
        self.moveConveyorItems()

        # Animate items moving to bins
        for data in list(self.animatedItems):
            item = data["item"]
            steps = data["steps"]
            data["currentStep"] += 1
            
           
            if data["currentStep"] >= steps:
                # Finalize position at bin
                item.setX(data["targetX"])
                item.setY(data["targetY"])
                self.animatedItems.remove(data)

                #remove items after 5 seconds of being sorted to save system memory 
                QTimer.singleShot(5000, lambda i=item: self.removeItemFromScene(i))
            else:
                dx = (data["targetX"] - item.x()) / (steps - data["currentStep"] + 1)
                dy = (data["targetY"] - item.y()) / (steps - data["currentStep"] + 1)
                item.setX(item.x() + dx)
                item.setY(item.y() + dy)

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














# -----------------
# Interactive Class
# -----------------
# class to make interactive boxes for user correction
class ClickableBox(QGraphicsRectItem):
    def __init__(self, width, height, size, taskParent, parent=None):
        super().__init__(0, 0, width, height, parent)
        self.size = size                  # store item size
        self.taskParent = taskParent      # reference to inspectionTask
        self.setBrush(QBrush(QColor(200, 200, 200)))
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)

    def mousePressEvent(self, event):
        print(f"Box clicked! Size = {self.size:.1f}")

        # Call overrideResult function in the parent task
        self.taskParent.overrideResult(self)

        # highlight box on click for visual feedback
        self.setBrush(QBrush(QColor(255, 255, 0)))  # yellow

        super().mousePressEvent(event)



        
