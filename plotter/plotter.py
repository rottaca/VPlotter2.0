import numpy as np
import re
import sys
import time

from multiprocessing import Process, Queue

from . import utils

def processPlotterQueue(plotter):
    plotter.processQueueAsync()
    
class BasePlotter:
    def __init__(self, calib, ):
        self.workerProcess = Process(target=processPlotterQueue, args=(self,))
        self.workerQueue = Queue(10)
        
        self.calib = calib
        self.currPos  = np.zeros((2,))
        self.currCordLength = calib.point2CordLength(self.currPos)
        self.speed = 1
        self.penIsDown = False
        self.workerProcess.start()
        
    def shutdown(self):
        print("Shutting down..")
        self.workerQueue.put(None) 
        self.workerQueue.close()
        self.workerQueue.join_thread()
        self.workerProcess.join()
        
    def executeGCodeFile(self, file):
        with open(file, 'r') as f:
            lines = f.readlines()
            
        for l in lines:
            self.workerQueue.put(l)
            
    def processQueueAsync():
        print("Plotter thread started")
        
        item = self.workerQueue.get()
        while(item is not None):
            self.executeCmd(item)
            item = self.workerQueue.get()
            
        print("Plotter thread stopped")
        exit(0)
    
    def executeCmd(self, cmd):
        # print("Process %s"%cmd)

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
            # print("Draw time: %f" % (end-start))
            
        if cmd.startswith("G28"):
            self.penUp()
            self.goToPos(np.array([0,0]))
            
        if cmd.startswith("M3"):
            self.penDown()
            
        if cmd.startswith("M4"):
            self.penUp()
            
    def goToPos(self, targetPos):
        if targetPos[0] < 0 or targetPos[1] < 0 or targetPos[0] > self.calib.base:
            print("Position out of range: %f x %f" % (targetPos[0],targetPos[1]))
            exit(1)
            
        # print("Move to %f x %f"%(targetPos[0],targetPos[1]))
        #sys.stdout.flush()

        # Bresenham line algorithm
        d = np.abs(targetPos - self.currPos)/self.calib.resolution
        d *= [1,-1]
        s = np.ones((2,))
        for i in range(2):
            if self.currPos[i] >= targetPos[i]:
                s[i] = -1
        err = d[0] + d[1]
        e2 = 0
                
        while(True):
            newCordLength = self.calib.point2CordLength(self.currPos)
            deltaCordLength = newCordLength - self.currCordLength
            deltaCordLength *= self.calib.stepsPerMM
            self.currCordLength = newCordLength

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
        self.penIsDown = False
        
    def penDown(self):
        self.penIsDown = True
            
        
    def setSpeed(self, s):
        # print("Set speed to %f" % s)
        self.speed = s
    
   
class SimulationPlotter(BasePlotter):
    def __init__(self, calib):
        self.points_x = []
        self.points_y = []
        BasePlotter.__init__(self, calib)
        
    def penUp(self):
        if self.penIsDown:
            self.points_x.append(self.currPos[0] + self.calib.origin[0])
            self.points_y.append(self.currPos[1] + self.calib.origin[1])
            self.points_x.append(np.nan)
            self.points_y.append(np.nan)
            
        super().penUp()
        
    def penDown(self):        
        if not self.penIsDown:
            self.points_x.append(self.currPos[0] + self.calib.origin[0])
            self.points_y.append(self.currPos[1] + self.calib.origin[1])
            
        super().penDown()
        
    def processQueueAsync(self):
        print("Plotter thread started")
        
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        plt.ion()
        plt.show()
        
        item = self.workerQueue.get()
        i = 0
        while(item is not None):
            self.executeCmd(item)
            item = self.workerQueue.get()
            
            if i % 1000 == 0:
                plt.cla()
                plt.plot(self.points_x,self.points_y)
                plt.scatter(0,0, 20, "g")
                plt.scatter(self.calib.origin[0],self.calib.origin[1], 20,"r")
                plt.gca().invert_yaxis()
                plt.plot([0, self.calib.base, self.calib.base, 0, 0],[0, 0, 700, 700, 0])
                plt.axis('equal')
                plt.draw()
                plt.pause(0.0001)
            
            i+=1
            
            
        print("Plotter thread stopped")
        exit(0)