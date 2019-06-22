
import sys
import time
import RPi.GPIO as GPIO
import numpy as np


def initMotorCtrl():
    GPIO.setmode(GPIO.BCM)
    # GPIO.setwarnings(False)


def cleanup():
    GPIO.cleanup()


class StepperCtrl:
    """ Stepper controller for multiple steppers that are controlled with individual pololu DRV8825 boards.
    """

    def __init__(self, dir_pins, step_pins, res_pins, micro_stepping=1):
        """The dimension of all parameters has to match the number of steppers (N):
         - dir_pins: N values
         - step_pins: N values
         - step_pins: N lists of 3 values for the 3 microstepping pins.
         """
        assert(len(dir_pins) == len(step_pins))
        assert(len(step_pins) == len(res_pins))

        self.dir_pins = dir_pins
        self.step_pins = step_pins
        self.res_pins = res_pins
        self.micro_stepping = micro_stepping

    def initGPIO(self):

        GPIO.setup(self.dir_pins, GPIO.OUT)
        GPIO.setup(self.step_pins, GPIO.OUT)

        for p in self.res_pins:
            GPIO.setup(p, GPIO.OUT)

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

    def doSteps(self, dirs, steps, stepDelay=0.00000001):
        """Execute steps on all stepper motors in parallel. 
        All movements are linearly interpolated and executed over the same timespan.
        Executing this movement requires approximately max(steps)*stepDelay seconds."""

        maxSteps = max(steps)
        chCnt = len(steps)
        GPIO.output(self.dir_pins, dirs)

        # Compute indices where we have to do a step
        # We have to figure out how to move the steppers
        # in order move them during the same timespan.
        step_pos = []
        for s in range(chCnt):
            step_pos.append(np.linspace(0, maxSteps-1, steps[s]))

        # Execute steps
        for i in range(maxSteps):
            for s in range(chCnt):
                if step_pos[s].shape[0] > 0 and step_pos[s][0] - i <= 0.5:
                    GPIO.output(self.step_pins[s], True)
                    GPIO.output(self.step_pins[s], False)

                    step_pos[s] = np.delete(step_pos[s], 0, 0)

                    time.sleep(stepDelay)


class ServoCtrl:
    """Controls a servo by using the GPIO.pwm class. """

    def __init__(self, pwm_pin, ctrl_freq=50, init_duty_cycle=0.1):
        self.ctrl_freq = ctrl_freq
        self.pwm_pin = pwm_pin
        self.init_duty_cycle = init_duty_cycle

    def initGPIO(self):
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pwm_pin, self.ctrl_freq)
        self.pwm.start(self.init_duty_cycle)

    def moveTo(self, duty_cycle, delay=0.3):
        """Set duty cycle in percent (0.0-100.0). This function 
        blocks for 'delay' seconds in order to wait for the servo
        to execute the move."""
        self.pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(delay)
