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
        self.speed = 10000
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
        print("Processing command: %s" % cmd)
        if cmd.startswith("G0"):
            d = gcode_generators.decodeGCode(cmd)
            if not d:
              return
              
            if "S" in d:
              self.setSpeed(d["S"])
              
            self.goToPos([d.get("X",self.currPos[0]), d.get("Y",self.currPos[1])])
            
        elif cmd.startswith("G28"):
            self.goToPos([0,0])
        elif cmd.startswith("M3"):
            self.penDown()
        elif cmd.startswith("M4"):
            self.penUp()
        else:
            print("Unexpected cmd type. Failed to process command.")
            #exit(0)
            
    def goToPos(self, targetPos):
        if targetPos[0] < 0 or targetPos[1] < 0 or targetPos[0] > self.calib.base:
            print("Position out of range: %f x %f" % (targetPos[0],targetPos[1]))
            exit(1)
        print("Target Pos: %d %d" % (targetPos[0], targetPos[1]))
        self.currPos = targetPos
        
    def penUp(self):
        self.penIsDown = False
        
    def penDown(self):
        self.penIsDown = True
        
    def setSpeed(self, s):
        print("Set speed to %f" % s)
        self.speed = s

import importlib
try:
    motorlib_loader = importlib.util.find_spec('RPi.GPIO')
except:
    motorlib_loader = None
    
if motorlib_loader is None:
    print("RPi.GPIO not found. HardwarePlotter not available.")
else:
    
    class HardwarePlotter(BasePlotter):
        def __init__(self, calib):
            self.servo_pos_up = config.PLOTTER_HARDWARE_CONFIG["servo_pos_up"]
            self.servo_pos_down= config.PLOTTER_HARDWARE_CONFIG["servo_pos_down"]
            BasePlotter.__init__(self, calib)
            
        def penUp(self):
            self.mcq.queuePenPos(self.servo_pos_up)
            #super().penUp()
            
        def penDown(self): 
            self.mcq.queuePenPos(self.servo_pos_down)
            #super().penDown()
                
        def goToPos(self, targetPos):
            if targetPos[0] < 0 or targetPos[1] < 0 or targetPos[0] > self.calib.base:
                print("Position out of range: %f x %f" % (targetPos[0],targetPos[1]))
                exit(1)
                
            #print("Convert movement to %d %d to steps." % (targetPos[0], targetPos[1]))
            
            #print("Move to %f x %f"%(targetPos[0],targetPos[1]))
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
                
                #print("---------- compute new step block ------------")
                #print("Current pos: %f %f" %(self.currPos[0], self.currPos[1]))
                #print("cord len: %f %f" %(newCordLength[0], newCordLength[1]))
                #print("deltaCordLength: %f %f" %(deltaCordLength[0], deltaCordLength[1]))
                
                
                # Round steps to integer
                deltaCordLength = (deltaCordLength*self.calib.stepsPerMM).astype(int)
                # Used rounded length as new lenth
                self.currCordLength = self.currCordLength + deltaCordLength/self.calib.stepsPerMM
                 
                self.mcq.queueStepperMove(deltaCordLength, self.speed)
                
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
            self.mcq = MotorCtrlQueue()
            self.mcq.start()
            
            i = 0       
            item = self.workerQueue.get()
            start = time.time()
            while(item is not None):
            
                #print("Processing cmd: %s" % item)
                self.executeCmd(item)
                
                i+=1
                if i % 1000 == 0:
                    print("Processed %d commands. %f ms per cmd. " % (i, (time.time()- start)*1000/i))
                       
                item = self.workerQueue.get()
            
            
            # Wait for stepper queue
            self.mcq.join()
            print("Plotter thread stopped")
            exit(0)        
    
    def runMovementExecutor(ctrlQueue):
        ctrlQueue.processMovementAsync()
        
    class MotorCtrlQueue():
        def __init__(self):
            self.workerProcessSteps = Process(target=runMovementExecutor, args=(self,))
            self.workerQueueSteps = Queue(100)
            
        def start(self):
            self.workerProcessSteps.start()
        
        def join(self):
            self.workerQueueSteps.put(None) 
            self.workerQueueSteps.close()
            self.workerQueueSteps.join_thread()
            self.workerProcessSteps.join()
            
        def processMovementAsync(self):
            print("Movement thread started")
            sys.stdout.flush()
            from . import motorctrl
            motorctrl.initMotorCtrl()
            
            # GPIO Pins
            dir_pins  = config.PLOTTER_HARDWARE_CONFIG["dir_pins"]
            step_pins = config.PLOTTER_HARDWARE_CONFIG["step_pins"]
            res_pins = config.PLOTTER_HARDWARE_CONFIG["res_pins"]
            micro_stepping = config.PLOTTER_HARDWARE_CONFIG["micro_stepping"]
            
            self.steppers = motorctrl.StepperCtrl(dir_pins, step_pins, [res_pins for i in range(2)],micro_stepping=micro_stepping)
            
            # GPIO Pins
            servo_pin = config.PLOTTER_HARDWARE_CONFIG["servo_pin"]
            self.servo_pos_up = config.PLOTTER_HARDWARE_CONFIG["servo_pos_up"]
            self.servo_pos_down= config.PLOTTER_HARDWARE_CONFIG["servo_pos_down"]
            
            self.servo = motorctrl.ServoCtrl(servo_pin, init_duty_cycle=self.servo_pos_up)
            
            self.steppers.initGPIO()
            self.servo.initGPIO()
            
            print("Waiting for movements")
            item = self.workerQueueSteps.get()
            start = time.time()
            while(item is not None):
                
                id = item[0]
                
                # Move stepper
                if id == 0:
                    #print("Execute steps %d %d" % (item[1][0], item[1][1]))
                   
                    unsigned_steps = [int(np.abs(i)) for i in item[1]]
                    dirs = [int(item[1][0]>0), int(item[1][1]<0)]
                    
                    if config.PLOTTER_HARDWARE_CONFIG["invert_step_dir"][0]:
                      dirs[0] = (~dirs[0] & 0x01)
                    if config.PLOTTER_HARDWARE_CONFIG["invert_step_dir"][1]:
                      dirs[1] = (~dirs[1] & 0x01)
                      
                    self.steppers.doSteps(dirs, unsigned_steps, 1/item[2]*micro_stepping)
                # Move pen
                elif id == 1:
                    #print("Execute pen move to %d"% (param))
                    self.servo.moveTo(item[1])
                else:
                    print("Unknown value")
                    exit(1)
                    
                       
                item = self.workerQueueSteps.get()
            
            motorctrl.cleanup()    
            print("Movement thread stopped")
            exit(0)
        
        def queuePenPos(self, pos):
            self.workerQueueSteps.put((1, pos))
            
        def queueStepperMove(self, move, speed):
            self.workerQueueSteps.put((0, move, speed))
            
try:
    matplotlib_loader = importlib.find_loader('matplotlib')
except:
    matplotlib_loader = None

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