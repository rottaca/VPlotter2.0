import numpy as np
import re
import sys
import time

from multiprocessing import Process, Queue

from . import utils

import matplotlib.pyplot as plt
points_x = []
points_y = []

plt.ion()
plt.show()

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

        
def operatePlotterAsync(plotter):
    print("Plotter thread started")
    
    item = plotter.workerQueue.get()
    while(item is not None):
        
        plotter.executeCmd(item)
        item = plotter.workerQueue.get()
        
    print("Plotter thread stopped")
    exit(0)
    
class Plotter:
    def __init__(self, calib):
        self.workerProcess = Process(target=operatePlotterAsync, args=(self,))
        self.workerQueue = Queue(10)
        
        self.calib = calib
        self.currPos  = np.zeros((2,))
        self.currCordLength = calib.point2CordLength(self.currPos)
        self.speed = 1
        
        self.workerProcess.start()
        
    def shutdown(self):
        print("Shutting down..")
        self.workerQueue.put(None) 
        self.workerQueue.close()
        self.workerQueue.join_thread()
        self.workerProcess.join()
        
    def executeCmd(self, cmd):
        print("Process %s"%cmd)

        if cmd.startswith("G0"):
            params = cmd.split()
            X = Y = 0
            for p in params:
                if p.startswith("X"):
                    X = float(p[1:])
                if p.startswith("Y"):
                    Y = float(p[1:])
                    
            start = time.time()
            self.goToPos(np.array([X,Y]))
            end = time.time()
            print("Draw time: %f" % (end-start))
            
        if cmd.startswith("G28"):
            self.penUp()
            self.goToPos(np.array([0,0]))
            self.penDown()
            
        if cmd.startswith("M3"):
            self.penDown()
            
        if cmd.startswith("M4"):
            self.penUp()
            
    
    def goToPos(self, targetPos):
        if targetPos[0] < 0 or targetPos[1] < 0 or targetPos[0] > self.calib.base:
            print("Position out of range: %f x %f" % (targetPos[0],targetPos[1]))
            exit(1) 
            
        print("Move to %f x %f"%(targetPos[0],targetPos[1]))
        sys.stdout.flush()

        # Bresenham line algorithm
        d = np.abs(targetPos - self.currPos)/self.calib.resolution
        d *= [1,-1]
        s = np.ones((2,))
        for i in range(2):
            if self.currPos[i] >= targetPos[i]:
                s[i] = -1
        err = d[0] + d[1]
        e2 = 0

        i = 0

        while(True):
            newCordLength = self.calib.point2CordLength(self.currPos)
            deltaCordLength = newCordLength - self.currCordLength
            deltaCordLength *= self.calib.stepsPerMM
            self.currCordLength = newCordLength

            points_x.append(self.currPos[0])
            points_y.append(self.currPos[1])

            if i % 1000 == 0:
                plt.cla()
                plt.plot(points_x,points_y)
                plt.draw()
                plt.pause(0.0001)
            i+=1

            # print("Set %f, %f"%(self.currPos[0],self.currPos[1]))
            # print("Length %f, %f"%(newCordLength[0],newCordLength[1]))
            # print("Steps: %d %d" % (deltaCordLength[0],deltaCordLength[1]))
            # print("Dist %f" % (np.linalg.norm(targetPos - self.currPos)))
            # sys.stdout.flush()
            
            # Are we close to our target point ?
            if(np.linalg.norm(targetPos - self.currPos) < self.calib.resolution):
                break
                
            e2 = 2*err
            if e2 > d[1]:
                err += d[1]
                self.currPos[0] += s[0]*self.calib.resolution
            if e2 < d[0]:
                err += d[0]
                self.currPos[1] += s[1]*self.calib.resolution
                
    def penUp(self):
        print("Pen up")
        time.sleep(0.5)
        
    def penDown(self):
        print("Pen down")
        time.sleep(0.5)
        
    def setSpeed(self, s):
        print("Set speed to %f" % s)
        self.speed = s
    
        
    