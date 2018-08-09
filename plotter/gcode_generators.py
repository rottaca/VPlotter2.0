import scipy as sp
import numpy as np
import imageio

def GCode_goTo(p, s=None):
    if s is not None:
        return "G0 X%f Y%f S%f" % (p[0],p[1], s)
    else:
        return "G0 X%f Y%f" % (p[0],p[1])
        
def GCode_home():
    return "G28"

def GCode_up():
    return "M4"
    
def GCode_down():
    return "M3"
    
def decodeGCode(gcode):
    params = gcode.split()
    data = {}
    try:
      for p in params:
          val = float(p[1:])
          key = p[0]
          data[key] = val
          
    except:
    
      print("Failed to decode command.")
      return {}
      
    return data

def postProcessGCode(gcode, minSegmentLen=1):
    init_size=len(gcode)
    gcode_old = gcode
    gcode_curr = []
    pos = None
    xRange = [np.iinfo(int).max, 0]
    yRange = [np.iinfo(int).max, 0]
    
    for code in gcode_old:
        if code.startswith("G0"):
        
            d = decodeGCode(code)
            newPos = np.array([d["X"], d["Y"]])
            if pos is None:
                pos = newPos
            elif np.linalg.norm(pos - newPos) < minSegmentLen:
                # print("Skipping segment of len %f" % (np.linalg.norm(pos - newPos)))
                continue
            else:
                pos = newPos
        
        elif code.startswith("G28"):
            pos = np.array([0,0])
        
        gcode_curr.append(code)
    
    gcode_old = list(gcode_curr)
    gcode_curr = []
    
    penDownCurr=None
    penDownNext=None
    
    for code in gcode_old:
        if code.startswith("G0") or code.startswith("G28"):
            if penDownCurr is None:
                if penDownNext is not None:
                
                    if penDownNext:
                        gcode_curr.append(GCode_down())
                    else:                    
                        gcode_curr.append(GCode_up())
                        
                    penDownCurr = penDownNext
                else:
                    print("Warning: initial pen position unknown! This could cause issues! Assuming pen is up")
                    penDownCurr=False
                    penDownNext=False
            else:
                if penDownCurr != penDownNext:
                    if penDownNext:
                        gcode_curr.append(GCode_down())
                    else:                    
                        gcode_curr.append(GCode_up())
                        
                    penDownCurr = penDownNext
                
            gcode_curr.append(code)
            
            d = decodeGCode(code)
            if "X" in d:
                if d["X"] < xRange[0]:
                    xRange[0] = d["X"]
                elif d["X"] > xRange[1]:
                    xRange[1] = d["X"]
            if "Y" in d:
                if d["Y"] < yRange[0]:
                    yRange[0] = d["Y"]
                elif d["Y"] > yRange[1]:
                    yRange[1] = d["Y"]
            
        elif code.startswith("M3"):
            penDownNext = True
        elif code.startswith("M4"):
            penDownNext = False
        else:
            gcode_curr.append(code)
            
    print("Reduced size from %d to %d lines of code. " % (init_size, len(gcode_curr)))
    print("Model bounding box is (%f, %f) x (%f, %f) mm. " % (xRange[0], yRange[0], xRange[1], yRange[1]))
    return gcode_curr
    
    
class GeneratorBase:
    def __init__(self):
        self.params = {
            "scale":1 ,
            "offset": np.array([0,0]),
            "speed_draw": 300000,
            "speed_nodraw": 50000
            }
    
    def updateParams(self, params):
        self.params.update(params)
        
    def convertImage(self, img):
        return np.array()
        
class StraightLineGenerator(GeneratorBase):
    def __init__(self):
        GeneratorBase.__init__(self)
        
    def convertImage(self, img):
        
        if len(img.shape) == 3 and img.shape[2] > 1:
            img = img.mean(axis = 2)
        
        gcode = [GCode_up(), GCode_home()]
        
        max_val = self.params["img_threshold_max"]
        min_val = self.params["img_threshold_min"]
        
        # Get pixel value and coordinates
        pixels = np.reshape(np.array(list(np.ndenumerate(img))),[img.shape[0], img.shape[1], 2])
        
        dirs_drawn = 0
        for d in self.params["dirs"]:
            indices = None
            
            if d == 1:
                indices = np.reshape(pixels, [-1,2], order='C')
            elif d == 2:
                # Flip columns and rows
                indices = np.reshape(pixels, [-1,2], order='F')
            elif d == 3:
                indices = []
                for y in range(img.shape[0]):
                    for x in range(np.min([y,img.shape[1]-1])):
                        indices.append(pixels[y-x,x,:])
                        
                for x in range(1,img.shape[1]):
                    for y in range(img.shape[1] - x):
                        indices.append(pixels[img.shape[0]-1-y,x+y,:])
                    
            elif d == 4:
                indices = []
                for y in range(img.shape[0]):
                    for x in range(np.min([img.shape[1]-y,img.shape[1]-1])):
                        indices.append(pixels[y+x,x,:])
                        
                for x in range(1,img.shape[1]):
                    for y in range(np.min([img.shape[1]-x,img.shape[1]-1])):
                        indices.append(pixels[y,x+y,:])
            
            drawing = False
            lastDrawPos = [0,0]
            lastY = 0
            lastX = 0
            
            for index, pixel in indices:
                y,x = index
                
                sameLine = False
                if np.abs(x - lastX) <= 1 and np.abs(y - lastY) <= 1:
                    sameLine = True
                
                if not sameLine and drawing:
                    pScreen = lastDrawPos*self.params["scale"] + self.params["offset"]
                    gcode.append(GCode_goTo(pScreen,self.params["speed_draw"]))
                    gcode.append(GCode_up())
                    drawing = False
                    
                lastY = y
                lastX = x
                
                pImg = np.array([x,y])
                
                if self.params["img_threshold_inv"]:
                    pixel = 255 - pixel
                    
                if pixel >= min_val and pixel <= max_val and pixel - min_val <= float(max_val - min_val)/(dirs_drawn+1):
                    if not drawing:
                        pScreen = pImg*self.params["scale"] + self.params["offset"]
                        gcode.append(GCode_goTo(pScreen,self.params["speed_nodraw"]))
                        gcode.append(GCode_down())
                        drawing = True
                else:
                    if drawing:
                        pScreen = lastDrawPos*self.params["scale"] + self.params["offset"]
                        gcode.append(GCode_goTo(pScreen,self.params["speed_draw"]))
                        gcode.append(GCode_up())
                        drawing = False
                   
                if drawing:
                    lastDrawPos = pImg
                    
            if drawing:
                pScreen = lastDrawPos*self.params["scale"] + self.params["offset"]
                gcode.append(GCode_goTo(pScreen,self.params["speed_draw"]))
                gcode.append(GCode_up())
                
            dirs_drawn = dirs_drawn + 1
        
        return gcode
        
class SinWaveGenerator(GeneratorBase):
    def __init__(self):
        GeneratorBase.__init__(self)
        
    def convertImage(self, img):
        
        if len(img.shape) == 3 and img.shape[2] > 1:
            img = img.mean(axis = 2)
        
        gcode = [GCode_up(), GCode_home()]
        
        lastY = 0
        
        pImg = np.array([0,0])
        pScreen = pImg*self.params["scale"] + self.params["offset"]
                      
        for index, pixel in np.ndenumerate(img):
            y,x = index
                        
            pImg = np.array([x,y + pixel/255*2*np.sin(x + 10*pixel/255)])
            pScreen = pImg*self.params["scale"] + self.params["offset"]
            
            if y != lastY:
                gcode.append(GCode_up())
                
            gcode.append(GCode_goTo(pScreen))
            
            if y != lastY:
                gcode.append(GCode_down())
                lastY = y
                
        return gcode        
        
class ArcGenerator(GeneratorBase):
    def __init__(self):
        GeneratorBase.__init__(self)
        
    def convertImage(self, img):
        
        if len(img.shape) == 3 and img.shape[2] > 1:
            img = img.mean(axis = 2)
        
        gcode = [GCode_up(), GCode_home()]
        
        lastY = 0
        
        pImg = np.array([0,0])
        pScreen = pImg*self.params["scale"] + self.params["offset"]
        maxRadius = np.linalg.norm(img.shape)
        
        for index, pixel in np.ndenumerate(img):
            y,x = index
                        
            pImg = np.array([x,y + pixel/255*2*np.sin(x + 10*pixel/255)])
            pScreen = pImg*self.params["scale"] + self.params["offset"]
            
            if y != lastY:
                gcode.append(GCode_up())
                
            gcode.append(GCode_goTo(pScreen))
            
            if y != lastY:
                gcode.append(GCode_down())
                lastY = y
                
        return gcode
        
class BoxGenerator(GeneratorBase):
    def __init__(self):
        GeneratorBase.__init__(self)
        
        
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
            pScreen = pImg*self.params["scale"] + self.params["offset"]
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
        pScreen = pImg*self.params["scale"] + self.params["offset"]
                
        for index, pixel in np.ndenumerate(img):
            if pixel > 0:
                y,x = index
                gcode.extend(self.drawBox(np.array([x,y]), pixel/255.0))
                
        return gcode
     
        
        
        
 