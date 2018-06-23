
import sys
import time
import RPi.GPIO as GPIO
import numpy as np

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.cleanup()

""" 
Stepper controller for multiple steppers that are controlled with individual pololu DRV8825 boards.
"""
class StepperCtrl:
    def __init__(self, dir_pins, step_pins, res_pins, micro_stepping=1):
        self.dir_pins=dir_pins
        self.step_pins=step_pins
        self.res_pins=res_pins       
        self.setMicrostepping(micro_stepping)
        
        GPIO.setup(self.dir_pins,GPIO.OUT)
        GPIO.setup(self.step_pins,GPIO.OUT)
        
        for p in self.res_pins:
            GPIO.setup(p,GPIO.OUT)
        
    def setMicrostepping(self, mstep):
        microstepping_map = {1: (0, 0, 0),
                                  2: (1, 0, 0),
                                  4: (0, 1, 0),
                                  8: (1, 1, 0),
                                  16: (0, 0, 1),
                                  32: (1, 0, 1)}
        self.micro_stepping = mstep
        GPIO.output(self.res_pins, microstepping_map[mstep])
        
    
    def doSteps(self, dirs, steps, stepDelay=0.0001):
        maxSteps=max(dirs)
        
        GPIO.output(self.dir_pins, dirs)
        
        # Compute indices where we have to do a step
        step_pos = []
        for s in len(steps):
            steps_pos[s] = np.linspace(0,maxSteps,steps[s])
            
        # Execute steps
        for i in range(maxSteps):
            for s in len(steps):
                if i >= steps_pos[s]:                    
                    GPIO.output(self.step_pins[s], True)
                    time.sleep(stepDelay)
                    GPIO.output(self.step_pins[s], False)
                    time.sleep(stepDelay)
    
class ServoCtrl:
    def __init__(self, pwm_pin, ctrl_freq=50, init_duty_cycle=0.1):
        self.ctrl_freq=ctrl_freq
        self.pwm = GPIO.PWM(pwm_pin, ctrl_freq)
        self.pwm.start(init_duty_cycle)
        
        
    def moveTo(self, duty_cycle, delay=0.01):
        self.pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(delay)