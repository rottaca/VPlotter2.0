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
    for code in gcode_old:
        if code.startswith("G0"):
        
            d = decodeGCode(code)
            newPos = np.array([d["X"], d["Y"]])
            if pos is None:
                pos = newPos
            elif np.linalg.norm(pos - newPos) < minSegmentLen:
                print("Skipping segment of len %f" % (np.linalg.norm(pos - newPos)))
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
        elif code.startswith("M3"):
            penDownNext = True
        elif code.startswith("M4"):
            penDownNext = False
        else:
            gcode_curr.append(code)
            
    print("Reduced size from %d to %d. " % (init_size, len(gcode_curr)))
    return gcode_curr
    
    
class GeneratorBase:
    def __init__(self):
        self.params = {
            "scale":1 ,
            "offset": np.array([0,0])
            }
    
    def updateParams(self, params):
        self.params.update(params)
        
    def convertImage(self, img):
        return np.array()
        
class BinaryGenerator(GeneratorBase):
    def __init__(self):
        GeneratorBase.__init__(self)
        
    def convertImage(self, img):
        
        if len(img.shape) == 3 and img.shape[2] > 1:
            img = img.mean(axis = 2)
        
        gcode = [GCode_up(), GCode_home()]
        speed_fast = 300000
        speed_slow = 50000
        drawing = False
        lastDrawPos = [0,0]
        lastY = 0
        
        for index, pixel in np.ndenumerate(img):
            y,x = index
            
            if y != lastY and drawing:
                pScreen = lastDrawPos*self.params["scale"] + self.params["offset"]
                gcode.append(GCode_goTo(pScreen,speed_slow))
                gcode.append(GCode_up())
                drawing = False
                
            lastY = y
            
            pImg = np.array([x,y])
            
            if pixel > 0:
                if not drawing:
                    pScreen = pImg*self.params["scale"] + self.params["offset"]
                    gcode.append(GCode_goTo(pScreen,speed_fast))
                    gcode.append(GCode_down())
                    drawing = True
            else:
                if drawing:
                    pScreen = lastDrawPos*self.params["scale"] + self.params["offset"]
                    gcode.append(GCode_goTo(pScreen,speed_slow))
                    gcode.append(GCode_up())
                    drawing = False
               
            if drawing:
                lastDrawPos = pImg
                
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
     
        
        
        
 