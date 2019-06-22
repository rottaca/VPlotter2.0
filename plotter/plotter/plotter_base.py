import numpy as np
import re
import sys
import time

from multiprocessing import Process, Queue

from plotter.utils.gcode import *
from plotter.utils.calibration import *


def processPlotterQueue(plotter):
    """Callback for plotter process."""
    plotter.processQueueAsync()


class BasePlotter:
    """Base class of all plotter implementations. Always call '__init__' in the derived class after
    setting up all (custom) member variables. Otherwise the (custom) config and calibration is
    not available in the worker process."""

    def __init__(self, config, initial_lengh, PhysicsEngineClass):
        """Sets up the worker process and initializes the system."""
        base = config["base_width"]
        self.calib = Calibration(base,
                                 PhysicsEngineClass.calcOrigin(
                                     initial_lengh, base),
                                 stepsPerMM=config["steps_per_mm"],
                                 resolution=config["movement_resolution"])

        self.config = config
        self.physicsEngine = PhysicsEngineClass(self.config, self.calib)
        self.currPos = np.zeros((2,))
        self.currCordLength = self.physicsEngine.point2CordLength(self.currPos)
        self.speed = 10000
        self.penIsDown = False

        self.workerProcess = Process(target=processPlotterQueue, args=(self,))
        self.workerQueue = Queue(1000)
        self.workerProcess.start()

    def shutdown(self):
        """Stops the worker queue and the worker process."""
        print("Shutting down..")
        self.workerQueue.put(None)
        self.workerQueue.close()
        self.workerQueue.join_thread()
        self.workerProcess.join()

    def executeGCodeFile(self, file_name):
        """Opens the specified gcode file and pushes each command into the worker queue.
        This will block if the queue is full."""
        with open(file_name, 'r') as f:
            lines = f.readlines()

        for c in lines:
            self.workerQueue.put(c.strip())

    def processQueueAsync(self):
        """Plotter worker function which runs in the worker process. 
        Processes new commands by reading from the worker queue."""
        print("Plotter process started")

        item = self.workerQueue.get()
        while(item is not None):

            self.executeCmd(item)

            item = self.workerQueue.get()

        print("Plotter process stopped")
        exit(0)

    def executeCmd(self, cmd):
        """Executes a command. Should only be called from the worker process."""

        if cmd.startswith("G0"):
            d = decodeGCode(cmd)
            if not d:
                return

            if "S" in d:
                self.setSpeed(d["S"])

            self.moveToPos([d.get("X", self.currPos[0]),
                            d.get("Y", self.currPos[1])])

        elif cmd.startswith("G28"):
            self.moveToPos([0, 0])

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

            self.moveArc([d["X"], d["Y"]], d["R"],
                         d.get("A", 0), d.get("B", 360))

        elif cmd.startswith("M3"):
            self.penDown()
        elif cmd.startswith("M4"):
            self.penUp()
        else:
            print("Unexpected cmd type. Failed to process command.")

    def moveToPos(self, targetPos):
        """Move to specified position. 
        Raises an error if not implemented by derived class."""
        raise NotImplementedError("Function moveToPos not implemented")

    def moveArc(self, center, radius, startAngle, endAngle):
        """Move on an arc. 
        Raises an error if not implemented by derived class."""
        raise NotImplementedError("Function moveArc not implemented")

    def penUp(self):
        """Lift the pen. 
        Raises an error if not implemented by derived class."""
        raise NotImplementedError("Function penUp not implemented")

    def penDown(self):
        """Lower the pen. 
        Raises an error if not implemented by derived class."""
        raise NotImplementedError("Function penDown not implemented")

    def setSpeed(self, s):
        """Sets the current speed. (used by subsequent commands)."""
        self.speed = s

    def __str__(self):
        return """
{}

------------ State ------------
Current Position: {}
Current Length:   {}
PenState:         {}
Current Speed:    {}
Queue Size:       {}
-------------------------------""".format(self.calib, self.currPos, self.currCordLength, "DOWN" if self.penIsDown else "UP", self.speed, self.workerQueue.qsize())
