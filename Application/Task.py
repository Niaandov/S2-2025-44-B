import random
from abc import ABC, abstractmethod

class Task(ABC):

    @property
    @abstractmethod
    def errorRate(self):
        pass

    @property
    @abstractmethod
    def speed(self):
        pass

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def renderTaskComponents(self):
        pass

    @abstractmethod
    def createNewBox(self):
        pass

    # Errors dealt with in advBoxQueue
    @abstractmethod
    def advBoxQueue(self):
        pass


    # Dedicates screen space and renders common components
    # Then calls overridden child class for rendering individual components
    # activeTasks and taskNumber is the amount of active tasks (1-3) self incl. and
    # the actual position of the task (1-3, where 1 = left of screen, 3 = right of screen, 2 = right or middle

    def renderScreenComponents(self, activeTasks, taskNumber):
        self.renderTaskComponents()
        pass

    def causeError(self):
        # Does this work? Does this make sense, I'll never tell~
        return self.errorRate + random.uniform(-0.25, 0.25) <= random.uniform(0.0,1.0)



