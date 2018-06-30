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
        print("Pos: %d %d" % (targetPos[0], targetPos[1]))
        self.currPos = targetPos
        
    def penUp(self):
        self.penIsDown = False
        
    def penDown(self):
        self.penIsDown = True
        
    def setSpeed(self, s):
        # print("Set speed to %f" % s)
        self.speed = s

import importlib
motorlib_loader = importlib.util.find_spec('RPi.GPIO')
if motorlib_loader is None:
    print("RPi.GPIO not found. HardwarePlotter not available.")
else:
    
    class HardwarePlotter(BasePlotter):
        def __init__(self, calib):
            BasePlotter.__init__(self, calib)
            
        def penUp(self):
            self.servo.moveTo(self.servo_pos_up)
            super().penUp()
            
        def penDown(self): 
            self.servo.moveTo(self.servo_pos_down)
            super().penDown()
                
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
            
            all_steps=[]
            all_dirs=[]
            
            while(True):
                newCordLength = self.calib.point2CordLength(self.currPos)
                deltaCordLength = newCordLength - self.currCordLength
                deltaCordLength *= self.calib.stepsPerMM
                self.currCordLength = newCordLength
                
                dirs = (deltaCordLength>0).tolist()
                dirs = [int(d) for d in dirs]
                
                steps = self.steppers.micro_stepping*deltaCordLength
                steps = [int(np.abs(i)) for i in steps.tolist()]
                
                all_steps.append(steps)
                all_dirs.append(dirs)                

                # print("Set %f, %f"%(self.currPos[0],self.currPos[1]))
                print("Length %f, %f"%(newCordLength[0],newCordLength[1]))
                #print("Steps: %d %d" % (deltaCordLength[0],deltaCordLength[1]))
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
                    
            for i in range(len(all_steps)):
                self.steppers.doSteps(all_dirs[i], all_steps[i])
                    
        def processQueueAsync(self):
            print("Plotter thread started")
            
            # GPIO Pins
            dir_pins  = config.PLOTTER_HARDWARE_CONFIG["dir_pins"]
            step_pins = config.PLOTTER_HARDWARE_CONFIG["step_pins"]
            res_pins = config.PLOTTER_HARDWARE_CONFIG["res_pins"]
            micro_stepping = config.PLOTTER_HARDWARE_CONFIG["micro_stepping"]
            
            servo_pin = config.PLOTTER_HARDWARE_CONFIG["servo_pin"]
            self.servo_pos_up = config.PLOTTER_HARDWARE_CONFIG["servo_pos_up"]
            self.servo_pos_down= config.PLOTTER_HARDWARE_CONFIG["servo_pos_down"]
            
            from . import motorctrl
            motorctrl.initMotorCtrl()
            
            self.steppers = motorctrl.StepperCtrl(dir_pins, step_pins, [res_pins for i in range(2)],micro_stepping=micro_stepping)
            self.servo = motorctrl.ServoCtrl(servo_pin, init_duty_cycle=self.servo_pos_up)
        
            self.steppers.initGPIO()
            self.servo.initGPIO()
            
            i = 0       
            item = self.workerQueue.get()
            start = time.time()
            while(item is not None):
            
                self.executeCmd(item)
                
                i+=1
                if i % 1000 == 0:
                    print("Processed %d commands. %f ms per cmd. " % (i, (time.time()- start)*1000/i))
                    
                item = self.workerQueue.get()
                
            motorctrl.cleanup()
                   
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