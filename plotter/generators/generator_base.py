import numpy as np

class GeneratorBase:
    """Generator base implementation."""
    def __init__(self, args):
        self.params = args
    
    @classmethod
    def getName(cls):
        """Return the name of this generator."""
        raise NotImplementedError()

    @classmethod
    def getHelp(cls):
        """Return a help message for your generator."""
        raise NotImplementedError()

    @classmethod
    def setupCustomParams(cls, subparser):
        """Specify custom commandline arguments for this generator."""
        raise NotImplementedError()

    def updateParams(self, params):
        self.params.update(params)
        
    def convertImage(self, img):
        """Actually convert an image into a code file."""
        return np.array()
        
    def px2Scr(self, p):
        """Transform a point from pixel coordinates to actual drawing coordinates."""
        return p*self.params["scale"] + self.params["offset"]