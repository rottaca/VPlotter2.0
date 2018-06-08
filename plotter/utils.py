import numpy as np


"""
Calibration class for plotter.
All (x,y) coordinates have to be relative to the origin.
Absolute zero is at the upper left corner (left motor).
"""
class Calibration:
    def __init__(self):
        self.origin = np.zeros((2,))
        self.base = 0
        self.mass = 0
        
    def computeCalibration(self, base, l, mass=0, stepsPerMM = 200, resolution=0.1):
        if base > np.sum(l):
            print("Invalid clalibration data specified")
            exit(1)
        self.base = base
        self.origin = self.cordLength2Point(l)
        self.mass = mass
        self.stepsPerMM = stepsPerMM
        self.resolution = resolution
        
    def __str__(self):
        return """----------Calibration----------
Base: {}
Origin: {}
Mass: {}""".format(str(self.base), str(self.origin), str(self.mass))
        
    def cordLength2Point(self, l):
        x = (self.base*self.base+l[0]*l[0]-l[1]*l[1])/(2*self.base)
        y = np.sqrt(l[1]*l[1] - (self.base-x)*(self.base-x))
        return np.array((x,y))
        
    def point2CordLength(self, p):
        l1 = np.linalg.norm(p + self.origin)
        l2 = np.linalg.norm(p + self.origin - np.array((self.base, 0)))
        return np.array((l1,l2))
        
    def computeCordStress(self, l, p):
        p = p + self.origin
        
        FG = 9.81*self.mass
        sinA = p[1]/l[0]
        sinB = p[1]/l[1]
        # TODO 
    