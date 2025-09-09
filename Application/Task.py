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
    def createNewBox(self):
        pass

    # Errors dealt with in advBoxQueue
    @abstractmethod
    def advBoxQueue(self):
        pass





