import numpy as np
import re
import sys
import time

from multiprocessing import Process, Queue

from . import utils
from . import gcode_generators
from . import config

def processPlotterQueue(plotter):
    plotter.processQueueAsync()
    
class BasePlotter:
    def __init__(self, calib):
        self.workerProcess = Process(target=processPlotterQueue, args=(self,))
        self.workerQueue = Queue(1000)
        
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
        
        for c in lines:
            self.workerQueue.put(c.strip())
            
    def processQueueAsync():
        print("Plotter thread started")
        
        item = self.workerQueue.get()
        while(item is not None):
        
            self.executeCmd(item)
                
            item = self.workerQueue.get()
            
        print("Plotter thread stopped")
        exit(0)
    
    def executeCmd(self, cmd):
        if cmd.startswith("G0"):
            d = gcode_generators.decodeGCode(cmd)
            self.goToPos([d["X"], d["Y"]])
        elif cmd.startswith("G28"):
            self.goToPos([0,0])
        elif cmd.startswith("M3"):
            self.penDown()
        elif cmd.startswith("M4"):
            self.penUp()
        else:
            print("Unexpected type read. Failed to process command.")
            exit(0)
            
    def goToPos(self, targetPos):
        if targetPos[0] < 0 or targetPos[1] < 0 or targetPos[0] > self.calib.base:
            print("Position out of range: %f x %f" % (targetPos[0],targetPos[1]))
            exit(1)
            
        self.currPos = targetPos
        
    def penUp(self):
        self.penIsDown = False
        
    def penDown(self):
        self.penIsDown = True
        
    def setSpeed(self, s):
        # print("Set speed to %f" % s)
        self.speed = s

import importlib
motorlib_loader = importlib.find_loader('RpiMotorLib')
if motorlib_loader is None:
    print("RpiMotorLib not found. HardwarePlotter not available.")
else:
    from RpiMotorLib import RpiMotorLib, rpiservolib
    
    class HardwarePlotter(BasePlotter):
        def __init__(self, calib):        
            # GPIO Pins
            dir_pins  = config.PLOTTER_HARDWARE_CONFIG["dir_pins"]
            step_pins = config.PLOTTER_HARDWARE_CONFIG["step_pins"]
            res_pins = config.PLOTTER_HARDWARE_CONFIG["res_pins"]
            
            self.res_type = "Full"
            self.res_type_map = {
                "Full": 1,
                "Half": 1/2.0,
                "1/4":  1/4.0,
                "1/8":  1/8.0,
                "1/16": 1/16.0,
                "1/32": 1/32.0
            }
            self.stepper = [
                RpiMotorLib.A4988Nema(dir_pins[0], step_pins[0], res_pins, "DRV8825"),
                RpiMotorLib.A4988Nema(dir_pins[1], step_pins[1], res_pins, "DRV8825")
            ]
             
            self.servo = rpiservolib.SG90servo("servoone", 50, 3, 11)
            self.servo_pin = config.PLOTTER_HARDWARE_CONFIG["servo_pin"]
            self.servo_pos_up = config.PLOTTER_HARDWARE_CONFIG["servo_pos_up"]
            self.servo_pos_down= config.PLOTTER_HARDWARE_CONFIG["servo_pos_down"]
            
            BasePlotter.__init__(self, calib)
            
        def penUp(self):
            self.servo.servo_move(self.servo_pin, self.servo_pos_up, 1, False, 0.01)
            super().penUp()
            
        def penDown(self): 
            self.servo.servo_move(self.servo_pin, self.servo_pos_down, 1, False, 0.01)
            super().penDown()
                
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
                
                for i in range(2):
                    self.stepper[i].motor_go(deltaCordLength[i]>0, self.res_type, int(deltaCordLength[i]/self.res_type_map[self.res_type]), 0.005, True, 0.05)

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
                    
        def processQueueAsync(self):
            print("Plotter thread started")
            
            i = 0       
            item = self.workerQueue.get()
            start = time.time()
            while(item is not None):
            
                self.executeCmd(item)
                
                i+=1
                if i % 1000 == 0:
                    print("Processed %d commands. %f ms per cmd. " % (i, (time.time()- start)*1000/i))
                    
                item = self.workerQueue.get()
                
                    
            print("Plotter thread stopped")
            exit(0)        
 
matplotlib_loader = importlib.find_loader('matplotlib')
if matplotlib_loader is None:
    print("Matplotlib not found. On-screen rendering not available.")
else:
    import matplotlib
    matplotlib.use('TkAgg')   # Use tk backend in our virtual environment
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    plt.ion()
    plt.show()  
    class SimulationPlotter(BasePlotter):
        def __init__(self, calib):
            self.points_x = []
            self.points_y = []
            self.pen_up_x = []
            self.pen_up_y = []
            self.pen_down_x = []
            self.pen_down_y = []
            
            BasePlotter.__init__(self, calib)
        
        def goToPos(self, targetPos):
            
            if targetPos[0] < 0 or targetPos[1] < 0 or targetPos[0] > self.calib.base:
                print("Position out of range: %f x %f" % (targetPos[0],targetPos[1]))
                exit(1)
                
            if self.penIsDown:
                self.points_x.append(self.currPos[0] + self.calib.origin[0])
                self.points_y.append(self.currPos[1] + self.calib.origin[1])
                
            super().goToPos(targetPos)
            
        def penUp(self):
            if self.penIsDown:
                self.points_x.append(self.currPos[0] + self.calib.origin[0])
                self.points_y.append(self.currPos[1] + self.calib.origin[1])
                self.points_x.append(np.nan)
                self.points_y.append(np.nan)
                self.pen_up_x.append(self.currPos[0] + self.calib.origin[0])
                self.pen_up_y.append(self.currPos[1] + self.calib.origin[1])
                
            super().penUp()

            
        def penDown(self):        
            if not self.penIsDown:
                self.points_x.append(self.currPos[0] + self.calib.origin[0])
                self.points_y.append(self.currPos[1] + self.calib.origin[1])
                self.pen_down_x.append(self.currPos[0] + self.calib.origin[0])
                self.pen_down_y.append(self.currPos[1] + self.calib.origin[1])
                
            super().penDown()

         
        def plotCurrentState(self):
            plt.cla()
            plt.plot(self.points_x,self.points_y)
            plt.scatter(0,0, 20, "g")
            plt.scatter(self.calib.origin[0],self.calib.origin[1], 20,"g")
            plt.plot([0, self.calib.base, self.calib.base, 0, 0],[0, 0, 700, 700, 0])
            # plt.scatter(self.pen_up_x,self.pen_up_y, 10,"m")
            # plt.scatter(self.pen_down_x,self.pen_down_y, 10,"c")
            plt.axis('equal')
            plt.gca().invert_yaxis()
            plt.draw()
            plt.pause(0.0001)
                
        def processQueueAsync(self):
            print("Plotter thread started")
            
            item = self.workerQueue.get()
            i = 0
            start = time.time()
            while(item is not None):
                self.executeCmd(item)
                
                i+=1
                if i % 1000 == 0:
                    print("Processed %d commands. %f ms per cmd. " % (i, (time.time()- start)*1000/i))
                    self.plotCurrentState()
                    
                
                item = self.workerQueue.get()
                    
            self.plotCurrentState()
            
            plt.show(block=True)    
                
            print("Plotter thread stopped")
            exit(0)