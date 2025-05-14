from enum import Enum
from datetime import datetime

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class Objective:
    def __init__(self, name, progress, color, position=None):
        self.name = name
        self.progress = progress
        self.color = color
        self.position = position

class Task:
    def __init__(self, title, description, objective, deadline, priority, id=None, position=None):
        self.id = id
        self.title = title
        self.description = description
        self.objective = objective
        self.deadline = deadline
        self.priority = priority
        self.position = position 