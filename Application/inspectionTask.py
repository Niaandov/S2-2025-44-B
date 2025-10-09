import random

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QFrame, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QPushButton

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
        # just call the item version
        self.createNewItem()

    def advBoxQueue(self):
        pass

    def createNewItem(self):
        size = random.uniform(8.0, 12.0)
        self.itemList.append(size)
        self.renderWindow.renderNewItem(size)

    def evaluateItem(self, size):
        return 8.0 <= size <= 12.0

    def performInspection(self):
        if not self.itemList:
            return

        #evalute the first item in the itemList queue
        actual_size = self.itemList[0]
        actual_result = self.evaluateItem(actual_size)

        # Apply random error (flip result when error procs)
        if self.causeError():
            result = not actual_result
        else:
            result = actual_result

        # Update metrics
        self.totalInspected += 1
        if result == actual_result:
            self.correctCount += 1
        elif actual_result is False and result is True:
            self.defectsMissed += 1

        # Visual feedback
        self.renderWindow.displayInspectionResult(actual_size, result)

        # Move to next item
        self.popItem()

    def startTask(self):
        # Create first item and start the conveyor
        self.createNewItem()
        self.renderWindow.startStuff(self._speed)


        self.itemTimer = QTimer()
        self.itemTimer.timeout.connect(self.createNewItem)
        self.itemTimer.start(int(1000)) #this will spawn a new Item every 1 second

    def popItem(self):
        if self.itemList:
            self.itemList.pop(0)

        #this can be changed the with the errorRate in task.py
    def causeError(self):
        error = self._errorRate + random.uniform(-0.05, 0.05) >= random.uniform(0.0, 1.0)
        return error

    def overrideResult(self, item):
        """Called from GUI click — user manually flips result"""
        print("User override triggered!")
        # Optional: you can also adjust metrics here if needed.

















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


        # ✅ Add Start button
        self.startButton = QPushButton("Start Simulation")
        layout.addWidget(self.startButton)

        # Connect button to startTask method
        self.startButton.clicked.connect(self.onStartClicked)
        

        # Animation setup
        self.conveyorItems = []     # Items moving along conveyor
        self.animatedItems = []     # Items moving to bins
        self.animTimer = QTimer()
        self.animTimer.timeout.connect(self.doAnimationStep)
        self.animTimer.start(50)

        # Pass/fail bin locations
        self.passBinX, self.passBinY = 50, -300
        self.failBinX, self.failBinY = self.sceneWidth - 150, -300

        # Animation parameters
        self.speed = 5  # default, will be updated by task speed
        self.pixelPerFrame = 2
        self.currentItem = None

    def onStartClicked(self):
        self.taskParent.startTask()
        self.startButton.setEnabled(False)


    def startStuff(self, speed):
        self.speed = speed
        self.pixelPerFrame = max(1, int(speed * 0.25))  # slower = smoother

    def renderNewItem(self, size):
        boxWidth = int((size / 15.0) * 100) + 20
        y = self.conveyorTopLocation + self.conveyorHeight / 4
        item = QGraphicsRectItem(0, y, boxWidth, 30)
        item.setBrush(QBrush(QColor(200, 200, 200)))
        item.setZValue(500)
        item.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.scene.addItem(item)
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
            # item will now animate via animatedItems list

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

        # Animate to bin instead of teleport
        steps = max(10, int(100 / self.speed))  # slower speed = more steps
        self.animatedItems.append({
            "item": self.currentItem,
            "targetX": targetX,
            "targetY": targetY,
            "steps": steps,
            "currentStep": 0
        })

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
            else:
                dx = (data["targetX"] - item.x()) / (steps - data["currentStep"] + 1)
                dy = (data["targetY"] - item.y()) / (steps - data["currentStep"] + 1)
                item.setX(item.x() + dx)
                item.setY(item.y() + dy)

    
