import numpy as np
import re
import sys
import time

from multiprocessing import Process, Queue

from plotter.utils.gcode import *
from plotter.utils.calibration import *


def processPlotterQueue(plotter):
    plotter.processQueueAsync()
    
class BasePlotter:
    def __init__(self, config, initial_lengh, PhysicsEngineClass):
        base = config["base_width"]
        self.calib = Calibration(base,
                                PhysicsEngineClass.calcOrigin(initial_lengh, base),
                                stepsPerMM=config["steps_per_mm"],
                                resolution=config["movement_resolution"])

        self.config = config
        self.physicsEngine = PhysicsEngineClass(self.config, self.calib)
        self.currPos  = np.zeros((2,))
        self.currCordLength = self.physicsEngine.point2CordLength(self.currPos)
        self.speed = 10000
        self.penIsDown = False

        self.workerProcess = Process(target=processPlotterQueue, args=(self,))
        self.workerQueue = Queue(1000)
        self.workerProcess.start()
    
    def __str__(self):
        return """
{}

------------ State ------------
Current Position: {}
Current Length:   {}
PenState:         {}
Current Speed:    {}
Queue Size:       {}""".format(self.calib, self.currPos, self.currCordLength, "DOWN" if self.penIsDown else "UP", self.speed, self.workerQueue.qsize())

    def shutdown(self):
        print("Shutting down..")
        self.workerQueue.put(None) 
        self.workerQueue.close()
        self.workerQueue.join_thread()
        self.workerProcess.join()
        
    def executeGCodeFile(self, file):
        with open(file, 'r') as f:
            lines = f.readlines()
        
        for c in lines:
            self.workerQueue.put(c.strip())
            
    def processQueueAsync(self):
        print("Plotter thread started")
        
        item = self.workerQueue.get()
        while(item is not None):
        
            self.executeCmd(item)
                
            item = self.workerQueue.get()
            
        print("Plotter thread stopped")
        exit(0)
    
    def executeCmd(self, cmd):
        # print("Processing command: %s" % cmd)
        if cmd.startswith("G0"):
            d = decodeGCode(cmd)
            if not d:
              return
              
            if "S" in d:
              self.setSpeed(d["S"])
              
            self.moveToPos([d.get("X",self.currPos[0]), d.get("Y",self.currPos[1])])
            
        elif cmd.startswith("G28"):
            self.moveToPos([0,0])

        elif cmd.startswith("G2"):
            d = decodeGCode(cmd)
            if not d:
              return
            
            if "S" in d:
              self.setSpeed(d["S"])
            
            if "R" not in d and "X" not in d and "Y" not in d:
                print(d)
                print("Unexpected cmd type. Failed to process command.")
                return
                
                
            self.moveArc([d["X"], d["Y"]], d["R"], d.get("A",0), d.get("B",360))
            
        elif cmd.startswith("M3"):
            self.penDown()
        elif cmd.startswith("M4"):
            self.penUp()
        else:
            print("Unexpected cmd type. Failed to process command.")
            #exit(0)
            
    def moveToPos(self, targetPos):        
        print("Function moveToPos not implemented")
        exit(1)
        
    def moveArc(self, center, radius, startAngle, endAngle):
        print("Function moveArc not implemented")
        exit(1)
        
    def penUp(self):
        print("Function penUp not implemented")
        exit(1)
        
    def penDown(self):
        print("Function penDown not implemented")
        exit(1)
        
    def setSpeed(self, s):
        self.speed = s
