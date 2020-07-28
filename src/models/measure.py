from enum import IntEnum


class Measure(IntEnum):
    """Measure enum (inherited from IntEnum)
    
    Values:
    0 = WARN
    1 = MUTE
    2 = KICK
    3 = BAN
    
    Functions:
    __int__(self) returns the integer value representing a certain measure
    __str__(self) returns the name of the measure"""
    WARN = 0
    MUTE = 1
    KICK = 2
    BAN = 3

    def __str__(self):
        """Returns the name of the measure
        Returns: 
        name:str = Name of measure"""
        return self.name
