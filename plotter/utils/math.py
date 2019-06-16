import numpy as np


class PhysicsEngine:
    def __init__(self, config, calib):
        self.config = config
        self.calib = calib

    @classmethod
    def calcOrigin(cls, l, base):
        """Converts the initial string lengths into the origin position.
        """
        raise NotImplementedError()
    
    def point2CordLength(self, p):
        """Converts a point in plotter coordinates into the left and right string length.
           Plotter coordinates are transformed into raw coordinates by adding the origin.
        """
        raise NotImplementedError()


class SimplePhysicsEngine(PhysicsEngine):
    def __init__(self, config, calib):
        PhysicsEngine.__init__(self, config, calib)

    @classmethod
    def calcOrigin(cls, l, base):
        """Converts the initial string lengths into the origin position.
        """

        if base > np.sum(l):
            print("Invalid clalibration data specified")
            exit(1)
            
        x = (base**2 + l[0]**2 - l[1]**2)/(2*base)
        y = np.sqrt(l[1]**2 - (base - x)**2)
        return np.array((x,y))
    
    def point2CordLength(self, p):
        """Converts a point in plotter coordinates into the left and right string length.
           Plotter coordinates are transformed into raw coordinates by adding the origin.
        """
        p_ = p + self.calib.origin
        l1 = np.sqrt(p_[0]**2 + p_[1]**2)
        l2 = np.sqrt((self.calib.base - p_[0])**2 + p_[1]**2)
        #l2 = np.linalg.norm([self.calib.base - p_[0], p_[1]])
        #print(p)
        #print(p_)
        return np.array((l1,l2))

