import numpy as np

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
        if code.startswith("G0"):
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
            
            # Find out bounding box of model
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
 
 