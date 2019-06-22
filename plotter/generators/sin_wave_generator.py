import numpy as np

from . import generator_base
from plotter.utils.gcode import *
from plotter.utils.helper import overrides


class SinWaveGenerator(generator_base.GeneratorBase):
    def __init__(self, args):
        generator_base.GeneratorBase.__init__(self, args)

    @classmethod
    def getName(cls):
        return "SinWave"

    @classmethod
    def getHelp(cls):
        return "Generates images by drawing sin waves."

    @classmethod
    def getInputType(cls):
        return "image"

    @classmethod
    def setupCustomParams(cls, subparser):
        pass

    @overrides(generator_base.GeneratorBase)
    def convert(self, img):

        if len(img.shape) == 3 and img.shape[2] > 1:
            img = img.mean(axis=2)

        gcode = [GCode_up(), GCode_home()]

        lastY = 0

        pImg = np.array([0, 0])
        pScreen = self.px2Scr(pImg)

        for index, pixel in np.ndenumerate(img):
            y, x = index

            pImg = np.array([x, y + pixel/255*2*np.sin(x + 10*pixel/255)])
            pScreen = self.px2Scr(pImg)

            if y != lastY:
                gcode.append(GCode_up())

            gcode.append(GCode_goTo(pScreen))

            if y != lastY:
                gcode.append(GCode_down())
                lastY = y

        return gcode
