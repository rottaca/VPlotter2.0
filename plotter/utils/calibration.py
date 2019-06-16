import numpy as np


class Calibration:
    """
    Calibration class for plotter.
    All (x,y) coordinates have to be relative to the origin.
    Absolute zero is at the upper left corner (left motor).
    """

    def __init__(self, base, origin, stepsPerMM, resolution):
        self.base = base
        self.origin = origin
        self.stepsPerMM = stepsPerMM
        self.resolution = resolution
        
    def __str__(self):
        return """----------Calibration----------
Base: {}
Origin: {}""".format(str(self.base), str(self.origin))


