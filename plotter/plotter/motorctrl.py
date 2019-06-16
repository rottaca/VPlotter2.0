
import sys
import time
import RPi.GPIO as GPIO
import numpy as np



def initMotorCtrl():
  GPIO.setmode(GPIO.BCM)
  #GPIO.setwarnings(False)
  
def cleanup():
  GPIO.cleanup() 

""" 
Stepper controller for multiple steppers that are controlled with individual pololu DRV8825 boards.
"""
class StepperCtrl:
    def __init__(self, dir_pins, step_pins, res_pins, micro_stepping=1):
        self.dir_pins=dir_pins
        self.step_pins=step_pins
        self.res_pins=res_pins       
                    
        self.micro_stepping = micro_stepping
    
    def initGPIO(self):
    
        GPIO.setup(self.dir_pins,GPIO.OUT)
        GPIO.setup(self.step_pins,GPIO.OUT)
        
        for p in self.res_pins:
            GPIO.setup(p,GPIO.OUT)
            
        self.setMicrostepping(self.micro_stepping)
        
    def setMicrostepping(self, mstep):
        microstepping_map = { 1: (0, 0, 0),
                              2: (1, 0, 0),
                              4: (0, 1, 0),
                              8: (1, 1, 0),
                             16: (0, 0, 1),
                             32: (1, 0, 1)}
        self.micro_stepping = mstep
        for p in self.res_pins:
          GPIO.output(p, microstepping_map[mstep])
        
    
    def doSteps(self, dirs, steps, stepDelay=0.00000001):
    
        #print("Steps: %d %d" % (steps[0],steps[1]))
        #print("Dirs: %d %d" %(dirs[0], dirs[1]))
        
        maxSteps=max(steps)
        chCnt = len(steps)
        GPIO.output(self.dir_pins, dirs)
        
        # Compute indices where we have to do a step
        step_pos = []
        for s in range(chCnt):
            step_pos.append(np.linspace(0,maxSteps-1,steps[s]))
        
        
        # Execute steps
        for i in range(maxSteps):
            for s in range(chCnt):
                if step_pos[s].shape[0] > 0 and step_pos[s][0] - i  <= 0.5:                    
                    GPIO.output(self.step_pins[s], True)
                    GPIO.output(self.step_pins[s], False)
                    
                    step_pos[s] = np.delete(step_pos[s], 0, 0) 
                    
                    time.sleep(stepDelay)
    
class ServoCtrl:
    def __init__(self, pwm_pin, ctrl_freq=50, init_duty_cycle=0.1):
        self.ctrl_freq=ctrl_freq
        self.pwm_pin=pwm_pin
        self.init_duty_cycle=init_duty_cycle
        
    def initGPIO(self):
        GPIO.setup(self.pwm_pin,GPIO.OUT)          
        self.pwm = GPIO.PWM(self.pwm_pin, self.ctrl_freq)
        self.pwm.start(self.init_duty_cycle)
        
        
    def moveTo(self, duty_cycle, delay=0.3):
        self.pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(delay)