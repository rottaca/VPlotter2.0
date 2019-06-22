import numpy as np
import sys
import time

from multiprocessing import Process, Queue

from . import plotter_base
from plotter.utils.helper import overrides

import importlib
try:
    motorlib_loader = importlib.util.find_spec('RPi.GPIO')
except:
    motorlib_loader = None

if motorlib_loader is None:
    print("RPi.GPIO not found. HardwarePlotter not available.")
else:

    class HardwarePlotter(plotter_base.BasePlotter):
        """Hardware plotter. The actual implementation which controls the steppers and the servo.
        This implementation uses the 3 interconnected processes in order to execute all required
        movements in a smooth way:
         - The main process is used to push gcode commands into the queue. (default behaviour of baseclass)
         - The plotter process parses a command, uses the Bresenham line algorithm to break down the move 
           into seperate short movements. (We can't do a simple linear interpolation due to the belt coordinate system).
           Linear interpolation is used for the short segments (<1 mm) after applying the bresenham algorithm.
         - These short segments are executed by parallel lienar interpolation of cord/belt lengths in the MotorControl process. 
           This process actually controls the stepper motors and the servo.
         """

        def __init__(self, config, initial_lengh, physicsEngineClass):
            self.servo_pos_up = config["servo_pos_up"]
            self.servo_pos_down = config["servo_pos_down"]

            plotter_base.BasePlotter.__init__(
                self, config, initial_lengh, physicsEngineClass)

        @overrides(plotter_base.BasePlotter)
        def penUp(self):
            self.mcq.queuePenPos(self.servo_pos_up)

        @overrides(plotter_base.BasePlotter)
        def penDown(self):
            self.mcq.queuePenPos(self.servo_pos_down)

        @overrides(plotter_base.BasePlotter)
        def moveToPos(self, targetPos):

            # Bresenham line algorithm
            # This algorithm is used to walk along a straight line on a
            # 2D plane in order to move from A(x,y) to B(x,y).
            # self.calib.resolution indicates the step size for this walking procedure.
            d = np.abs(targetPos - self.currPos)/self.calib.resolution
            d *= [1, -1]
            s = np.ones((2,))
            for i in range(2):
                if self.currPos[i] >= targetPos[i]:
                    s[i] = -1
            err = d[0] + d[1]
            e2 = 0

            while(True):
                newCordLength = self.physicsEngine.point2CordLength(
                    self.currPos)
                deltaCordLength = newCordLength - self.currCordLength

                # Round steps to integer
                deltaCordLength = (
                    deltaCordLength*self.calib.stepsPerMM).astype(int)
                # Used rounded length as new lenth
                self.currCordLength = self.currCordLength + \
                    deltaCordLength/self.calib.stepsPerMM

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

        @overrides(plotter_base.BasePlotter)
        def processQueueAsync(self):
            """Override the default behavior because we need to 
            launch an additional process for the MotorCtrl process.
            This process has to be connected to the plotter process."""
            print("Plotter process started")
            self.mcq = MotorCtrlQueue(self.config)
            self.mcq.start()

            i = 0
            item = self.workerQueue.get()
            start = time.time()
            while(item is not None):

                self.executeCmd(item)

                i += 1
                if i % 1000 == 0:
                    print("Processed %d commands. %f ms per cmd. " %
                          (i, (time.time() - start)*1000/i))

                item = self.workerQueue.get()

            # Wait for stepper queue
            self.mcq.join()
            print("Plotter process stopped")
            exit(0)

    def runMovementExecutor(ctrlQueue):
        """Callback function for the motor control process."""
        ctrlQueue.processMovementAsync()

    class MotorCtrlQueue():
        def __init__(self, config):
            self.workerProcessSteps = Process(
                target=runMovementExecutor, args=(self,))
            self.workerQueueSteps = Queue(100)
            self.config = config

        def start(self):
            self.workerProcessSteps.start()

        def join(self):
            self.workerQueueSteps.put(None)
            self.workerQueueSteps.close()
            self.workerQueueSteps.join_thread()
            self.workerProcessSteps.join()

        def processMovementAsync(self):
            """Converts the queued movements from mm to actual steps and executes the movements."""
            print("Movement process started")
            sys.stdout.flush()
            from . import motorctrl
            motorctrl.initMotorCtrl()

            # GPIO Pins
            dir_pins = self.config["dir_pins"]
            step_pins = self.config["step_pins"]
            res_pins = self.config["res_pins"]
            micro_stepping = self.config["micro_stepping"]

            self.steppers = motorctrl.StepperCtrl(
                dir_pins, step_pins, [res_pins for i in range(2)], micro_stepping=micro_stepping)

            # GPIO Pins
            servo_pin = self.config["servo_pin"]
            self.servo_pos_up = self.config["servo_pos_up"]
            self.servo_pos_down = self.config["servo_pos_down"]

            self.servo = motorctrl.ServoCtrl(
                servo_pin, init_duty_cycle=self.servo_pos_up)

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
                    dirs = [int(item[1][0] > 0), int(item[1][1] < 0)]

                    if self.config["invert_step_dir"][0]:
                        dirs[0] = (~dirs[0] & 0x01)
                    if self.config["invert_step_dir"][1]:
                        dirs[1] = (~dirs[1] & 0x01)

                    self.steppers.doSteps(
                        dirs, unsigned_steps, 1/item[2]*micro_stepping)
                # Move pen
                elif id == 1:
                    #print("Execute pen move to %d"% (param))
                    self.servo.moveTo(item[1])
                else:
                    print("Unknown value")
                    exit(1)

                item = self.workerQueueSteps.get()

            motorctrl.cleanup()
            print("Movement process stopped")
            exit(0)

        def queuePenPos(self, pos):
            self.workerQueueSteps.put((1, pos))

        def queueStepperMove(self, move, speed):
            self.workerQueueSteps.put((0, move, speed))
