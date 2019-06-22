import numpy as np
import time
from plotter.utils.helper import overrides
from . import plotter_base

import importlib
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

    plt.ion()
    plt.show() 
    class SimulationPlotter(plotter_base.BasePlotter):
        """Simulation plotter implementation. Renderes movements to a matplotlib figure."""
        def __init__(self, config, initial_lengh, physicsEngineClass, sim_speed, sim_plot_interval, non_drawing_moves):
            self.points_x = []
            self.points_y = []
            self.points_x_nodraw = []
            self.points_y_nodraw = []
            self.pen_up_x = []
            self.pen_up_y = []
            self.pen_down_x = []
            self.pen_down_y = []
            self.non_drawing_moves = non_drawing_moves
            self.sim_speed = sim_speed
            self.sim_plot_interval = sim_plot_interval
            plotter_base.BasePlotter.__init__(self, config, initial_lengh, physicsEngineClass)

        @overrides(plotter_base.BasePlotter)
        def moveToPos(self, targetPos):             
            if self.penIsDown:
                self.points_x.append(self.currPos[0] + self.calib.origin[0])
                self.points_y.append(self.currPos[1] + self.calib.origin[1])
            elif self.non_drawing_moves:
                self.points_x_nodraw.append(self.currPos[0] + self.calib.origin[0])
                self.points_y_nodraw.append(self.currPos[1] + self.calib.origin[1])
                
            self.currPos = targetPos
                
        @overrides(plotter_base.BasePlotter)
        def penUp(self):
            if self.penIsDown:
                self.points_x.append(self.currPos[0] + self.calib.origin[0])
                self.points_y.append(self.currPos[1] + self.calib.origin[1])
                self.points_x.append(np.nan)
                self.points_y.append(np.nan)
                self.pen_up_x.append(self.currPos[0] + self.calib.origin[0])
                self.pen_up_y.append(self.currPos[1] + self.calib.origin[1])
            elif self.non_drawing_moves:
                self.points_x_nodraw.append(self.currPos[0] + self.calib.origin[0])
                self.points_y_nodraw.append(self.currPos[1] + self.calib.origin[1])
            
            self.penIsDown = False

        @overrides(plotter_base.BasePlotter)
        def penDown(self):        
            if not self.penIsDown:
                self.points_x.append(self.currPos[0] + self.calib.origin[0])
                self.points_y.append(self.currPos[1] + self.calib.origin[1])
                self.pen_down_x.append(self.currPos[0] + self.calib.origin[0])
                self.pen_down_y.append(self.currPos[1] + self.calib.origin[1])
            elif self.non_drawing_moves:
                self.points_x.append(self.currPos[0] + self.calib.origin[0])
                self.points_y.append(self.currPos[1] + self.calib.origin[1])
                self.points_x_nodraw.append(np.nan)
                self.points_y_nodraw.append(np.nan)
                
            self.penIsDown = True

         
        def plotCurrentState(self):
            plt.cla()
            if self.non_drawing_moves:
                plt.plot(self.points_x_nodraw,self.points_y_nodraw,'r')
            plt.plot(self.points_x,self.points_y,'b')
            plt.scatter(0,0, 20, "g")
            plt.scatter(self.calib.origin[0],self.calib.origin[1], 20,"g")
            plt.plot([0, self.calib.base, self.calib.base, 0, 0],[0, 0, 700, 700, 0])
            # plt.scatter(self.pen_up_x,self.pen_up_y, 10,"m")
            # plt.scatter(self.pen_down_x,self.pen_down_y, 10,"c")
            plt.axis('equal')
            plt.gca().invert_yaxis()
            plt.draw()
            plt.pause(self.sim_speed)
             
        @overrides(plotter_base.BasePlotter)
        def processQueueAsync(self):
            print("Plotter thread started")
            
            item = self.workerQueue.get()
            i = 0
            start = time.time()
            while(item is not None):
                self.executeCmd(item)
                
                i+=1
                if i % self.sim_plot_interval == 0:
                    print("Processed %d commands. %f ms per cmd. " % (i, (time.time()- start)*1000/i))
                    self.plotCurrentState()
                    
                
                item = self.workerQueue.get()
                    
            self.plotCurrentState()
            
            plt.show(block=True)    
                
            print("Plotter thread stopped")
            exit(0)