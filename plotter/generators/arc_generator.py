import numpy as np

from . import generator_base
from plotter.utils.gcode import *
from plotter.utils.helper import overrides

class ArcGenerator(generator_base.GeneratorBase):
    def __init__(self, args):
        generator_base.GeneratorBase.__init__(self, args)
        
    @classmethod
    def getName(cls):
        return "Arc"

    @classmethod
    def getHelp(cls):
        return "Generates images by drawing arcs."

    @classmethod
    def setupCustomParams(cls, subparser):
        subparser.add_argument('--img-threshold-min', default=0, type=int, help="Min threshold for image.")
        subparser.add_argument('--img-threshold-max', default=255, type=int, help="Max threshold for image.")
        subparser.add_argument('--img-threshold-inv', default=False, action="store_true", help="Invert image thresholding.")
        subparser.add_argument('--dirs', default=[1], nargs="*", type=int, choices=[1,2,3,4], help="List of directions that should be used for drawing")
        subparser.add_argument('--arc_sampling', default=20, type=int, help="Number of samples per arc.")

    @overrides(generator_base.GeneratorBase)
    def convertImage(self, img):
        
        if len(img.shape) == 3 and img.shape[2] > 1:
            img = img.mean(axis = 2)
        
        gcode = [GCode_up(), GCode_home()]
        
        
        max_val = self.params["img_threshold_max"]
        min_val = self.params["img_threshold_min"]
        maxRadius = int(np.linalg.norm(img.shape))
        
        dirs_drawn = 0
        for d in self.params["dirs"]:
            pImg = np.array([0,0])
            pScreen = self.px2Scr(pImg)
            
            if d == 1:
                offset = np.array([0,0])
            elif d == 2:
                offset = np.array([img.shape[1]-1,0])
            elif d == 3:
                offset = np.array([0,img.shape[0]-1])
            elif d == 4:
                offset = np.array([img.shape[1]-1,img.shape[0]-1])
            
            for r in range(1,maxRadius):
                gcode.append(GCode_up())
                drawing = False
                lastDrawPos = [0,0]
                
                # Sample in such a way that each arc segment has the same length
                # arc_length = 2*pi*r*radians/(2*pi)
                # radians = arc_length/r
                sampling = self.params["arc_sampling"]/r
                # print(sampling)
                
                if d == 1:
                    angles = np.arange(0,90,sampling)
                elif d == 2:
                    angles = np.arange(0,-90,-sampling)
                elif d == 3:
                    angles = np.arange(90,180,sampling)
                elif d == 4:
                    angles = np.arange(-90,-180,-sampling)
            
                for a in angles:
                    pImg = np.array([r*np.sin(np.radians(a)),r*np.cos(np.radians(a))])
                    pImg = pImg + offset
                    
                    if pImg[0] < -0.5 or pImg[1] < -0.5 or pImg[1] >= img.shape[0]-0.5 or pImg[0] >= img.shape[1]-0.5:
                        continue
                        
                    pixel = img[int(pImg[1]),int(pImg[0])]
                                            
                    if self.params["img_threshold_inv"]:
                        pixel = 255 - pixel
                        
                    if pixel >= min_val and pixel <= max_val and pixel - min_val <= float(max_val - min_val)/(dirs_drawn+1):
                        pScreen = self.px2Scr(pImg)
                        gcode.append(GCode_goTo(pScreen,self.params["speed_nodraw"]))
                        
                        if not drawing:
                            gcode.append(GCode_down())
                            drawing = True
                        
                    else:
                        if drawing:
                            pScreen = self.px2Scr(lastDrawPos)
                            gcode.append(GCode_goTo(pScreen,self.params["speed_draw"]))
                            gcode.append(GCode_up())
                            drawing = False
                       
                    if drawing:
                        lastDrawPos = pImg           
                    
            
            dirs_drawn = dirs_drawn + 1
            
        return gcode
   