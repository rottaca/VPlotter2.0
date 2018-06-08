import scipy as sp
import numpy as np
import imageio

class GCodeGenerator:
    def __init__(self):
        pass
        
    def goTo(self,p):
        return "G0 X%f Y%f" % (p[0],p[1])
    
    def home(self):
        return "G28"
    
    def penUp(self):
        return "M4"
        
    def penDown(self):
        return "M3"


class GeneratorBase:
    def __init__(self):
        self.params = {"scale":2 , "offset": np.array([0,0])}
        self.generator = GCodeGenerator()
    
    def updateParams(self, params):
        self.params.update(params)
    
    def convertImage(self, img):
        pass
        
class BinaryGenerator(GeneratorBase):
    def __init__(self):
        GeneratorBase.__init__(self)
        self.updateParams({"threshold":128})
        
    def convertImage(self, img):
        gcode = []
        
        img = img.mean(axis = 2)
        
        import matplotlib.pyplot as plt

        plt.imshow(img>self.params["threshold"])
        plt.gray()
        plt.show(block=False)
        plt.pause(0.001)
        
        gcode.append(self.generator.penUp())
        gcode.append(self.generator.home())
        drawing = False
        lastDrawPos = [0,0]
        lastY = 0
        
        for index, pixel in np.ndenumerate(img):
            y,x = index
            
            if y != lastY and drawing:
                pScreen = lastDrawPos*self.params["scale"] + self.params["offset"]
                gcode.append(self.generator.goTo(pScreen))
                gcode.append(self.generator.penUp())
                drawing = False
                
            lastY = y
            
            pImg = np.array([x,y])
            
            if pixel > self.params["threshold"]:
                if not drawing:
                    pScreen = pImg*self.params["scale"] + self.params["offset"]
                    gcode.append(self.generator.goTo(pScreen))
                    gcode.append(self.generator.penDown())
                    drawing = True
            else:
                if drawing:
                    pScreen = lastDrawPos*self.params["scale"] + self.params["offset"]
                    gcode.append(self.generator.goTo(pScreen))
                    gcode.append(self.generator.penUp())
                    drawing = False
               
            if drawing:
                lastDrawPos = pImg
                
        return gcode
        
        
        
 