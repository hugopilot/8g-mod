import enum
from enum import IntEnum

class Measure(IntEnum):
    WARN = 0
    MUTE = 1
    KICK = 2
    BAN = 3

    def __str__(self):
        return self.name
