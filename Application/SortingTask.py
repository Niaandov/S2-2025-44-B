import random

from Task import Task

class SortingTask(Task):
    def __init__(self, errorRateVal, speed, numColours):
        self._errorRate = errorRateVal
        self._speed = speed
        self.numColours = numColours
        self.boxList = []
        self.errorDict = {}

        self.redError = 0
        self.blueError = 0
        if self.numColours > 2:
            self.greenError = 0


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
        self.boxList.append(self.getRandomColour())
        print(self.boxList)


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

        print(self.boxList)
        self.boxList.pop(0)




        # Some rendering anim goes here.
        # Probable process is:
            # Get arm into position to 'pick up' the box
            # Change sprite of arm to include a box with a new colour
            # Remove box on conveyor belt
            # Move box into the right hub
            # Enable box sprite in the hub
            # Colour is decided by current thing

    def renderTaskComponents(self):
        pass


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


