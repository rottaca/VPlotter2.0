
import sys
import time
import RPi.GPIO as GPIO
import numpy as np



def initMotorCtrl():
  GPIO.setmode(GPIO.BCM)
  #GPIO.setwarnings(False)

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
        microstepping_map = {1: (0, 0, 0),
                                  2: (1, 0, 0),
                                  4: (0, 1, 0),
                                  8: (1, 1, 0),
                                  16: (0, 0, 1),
                                  32: (1, 0, 1)}
        self.micro_stepping = mstep
        for p in self.res_pins:
          GPIO.output(p, microstepping_map[mstep])
        
    
    def doSteps(self, dirs, steps, stepDelay=0.0001):
        maxSteps=max(dirs)
        chCnt = len(steps)
        GPIO.output(self.dir_pins, dirs)
        
        # Compute indices where we have to do a step
        step_pos = []
        for s in range(chCnt):
            st = np.abs(steps[s])
            step_pos.append(np.linspace(0,maxSteps,st))
            
        # Execute steps
        for i in range(maxSteps):
            for s in range(chCnt):
                if i >= step_pos[s][0]:                    
                    GPIO.output(self.step_pins[s], True)
                    time.sleep(stepDelay)
                    GPIO.output(self.step_pins[s], False)
                    time.sleep(stepDelay)
                    step_pos[s] = step_pos[s][1:]
    
class ServoCtrl:
    def __init__(self, pwm_pin, ctrl_freq=50, init_duty_cycle=0.1):
        self.ctrl_freq=ctrl_freq
        self.pwm_pin=pwm_pin
        
    def initGPIO(self):
        GPIO.setup(self.pwm_pin,GPIO.OUT)          
        self.pwm = GPIO.PWM(self.pwm_pin, self.ctrl_freq)
        self.pwm.start(1)
        
        
    def moveTo(self, duty_cycle, delay=1):
        self.pwm.ChangeDutyCycle(100)
        time.sleep(delay)