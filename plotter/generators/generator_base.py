import numpy as np

class GeneratorBase:
    def __init__(self, args):
        self.params = args
    
    @classmethod
    def getName(cls):
        raise NotImplementedError()

    @classmethod
    def getHelp(cls):
        raise NotImplementedError()

    @classmethod
    def setupCustomParams(cls, subparser):
        raise NotImplementedError()

    def updateParams(self, params):
        self.params.update(params)
        
    def convertImage(self, img):
        return np.array()
        
    def px2Scr(self, p):
        return p*self.params["scale"] + self.params["offset"]