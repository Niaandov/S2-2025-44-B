import random
from abc import ABC, abstractmethod

from PyQt5.QtWidgets import QGraphicsItem


class Task(ABC):


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



