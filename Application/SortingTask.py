import random

from Task import Task

class SortingTask(Task):
    def __init__(self, errorRate, speed, numColours):
        self.errorRate = errorRate
        self.speed = speed
        self.numColours = numColours
        self.boxList = []
        self.errorDict = {}

    @property
    def speed(self):
        return self.speed

    @speed.setter
    def speed(self, value):
        self.speed = value

    @property
    def errorRate(self):
        return self.errorRate

    @errorRate.setter
    def errorRate(self, value):
        self.errorRate = value

    def createNewBox(self):
        self.boxList.append(self.getRandomColour())

    # STATUS 1/09/2025:
    # Not sure how to store errors. I want to use a key/value pair, storing the colour and the current box
    # But Dict don't work for that
    # ALT METHODS:
    # Create lists for each box, store a value in that, empty if no errors occur
    # More mem intensive, less comp/search intensive(?)
    def advBoxQueue(self):
        if self.causeError():
            print("error :)")
        else:
            print("no error :)")

    def renderTaskComponents(self):
        pass


    def getRandomColour(self):
        match random.randint(0,2):
            case 0:
                return "#ff0000"
            case 1:
                return "#00ff00"
            case 2:
                return "#0000ff"
            case _:
                return "#0000ff"





