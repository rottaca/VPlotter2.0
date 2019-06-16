import numpy as np

from . import generator_base
from plotter.utils.gcode import *

class BoxGenerator(generator_base.GeneratorBase):
    def __init__(self, args):
        generator_base.GeneratorBase.__init__(self, args)
        
    @classmethod
    def getName(cls):
        return "Box"

    @classmethod
    def getHelp(cls):
        return "Generates images by drawing boxes."

    @classmethod
    def setupCustomParams(cls, subparser):
        pass

    def drawBox(self, c, v):
        points = [
            np.array((-0.5, -0.5)),
            np.array((-0.5,  0.5)),
            np.array(( 0.5,  0.5)),
            np.array(( 0.5, -0.5)),
            np.array((-0.5, -0.5))
        ]
        
        gcode = []
        for p in points:
            pImg = p*v + c
            pScreen = self.px2Scr(pImg)
            gcode.append(GCode_goTo(pScreen))
            
            if len(gcode) == 1: 
                gcode.append(GCode_down())
        
        gcode.append(GCode_up())
        
        return gcode
        
    def convertImage(self, img):
        
        if len(img.shape) == 3 and img.shape[2] > 1:
            img = img.mean(axis = 2)
        
        gcode = [GCode_up(), GCode_home()]
        
        lastY = 0
        
        pImg = np.array([0,0])
        pScreen = self.px2Scr(pImg)
                
        for index, pixel in np.ndenumerate(img):
            if pixel > 0:
                y,x = index
                gcode.extend(self.drawBox(np.array([x,y]), pixel/255.0))
                
        return gcode
     
        
        
        
 