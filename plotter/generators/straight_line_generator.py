import numpy as np

from . import generator_base
from plotter.utils.gcode import *
from plotter.utils.helper import overrides


class StraightLineGenerator(generator_base.GeneratorBase):
    def __init__(self, args):
        generator_base.GeneratorBase.__init__(self, args)

    @classmethod
    def getName(cls):
        return "StraightLine"

    @classmethod
    def getHelp(cls):
        return "Generates images by drawing straight lines."

    @classmethod
    def getInputType(cls):
        return "image"

    @classmethod
    def setupCustomParams(cls, subparser):
        subparser.add_argument(
            '--img-threshold-min', default=0, type=int, help="Min threshold for image.")
        subparser.add_argument(
            '--img-threshold-max', default=255, type=int, help="Max threshold for image.")
        subparser.add_argument('--img-threshold-inv', default=False,
                               action="store_true", help="Invert image thresholding.")
        subparser.add_argument('--dirs', default=[1], nargs="*", type=int, choices=[
                               1, 2, 3, 4], help="List of directions that should be used for drawing")

    @overrides(generator_base.GeneratorBase)
    def convert(self, img):

        if len(img.shape) == 3 and img.shape[2] > 1:
            img = img.mean(axis=2)

        gcode = [GCode_up(), GCode_home()]

        max_val = self.params["img_threshold_max"]
        min_val = self.params["img_threshold_min"]

        # Get pixel value and coordinates
        pixels = np.reshape(np.array(list(np.ndenumerate(img))), [
                            img.shape[0], img.shape[1], 2])

        dirs_drawn = 0
        for d in self.params["dirs"]:
            indices = None

            if d == 1:
                indices = np.reshape(pixels, [-1, 2], order='C')
            elif d == 2:
                # Flip columns and rows
                indices = np.reshape(pixels, [-1, 2], order='F')
            elif d == 3:
                indices = []
                for y in range(img.shape[0]):
                    for x in range(np.min([y, img.shape[1]-1])):
                        indices.append(pixels[y-x, x, :])

                for x in range(1, img.shape[1]):
                    for y in range(img.shape[1] - x):
                        indices.append(pixels[img.shape[0]-1-y, x+y, :])

            elif d == 4:
                indices = []
                for y in range(img.shape[0]):
                    for x in range(np.min([img.shape[1]-y, img.shape[1]-1])):
                        indices.append(pixels[y+x, x, :])

                for x in range(1, img.shape[1]):
                    for y in range(np.min([img.shape[1]-x, img.shape[1]-1])):
                        indices.append(pixels[y, x+y, :])

            drawing = False
            lastDrawPos = [0, 0]
            lastY = 0
            lastX = 0

            for index, pixel in indices:
                y, x = index

                sameLine = False
                # Change in x or y > 1 or not ?
                if np.abs(x - lastX) <= 1 and np.abs(y - lastY) <= 1:
                    sameLine = True

                if not sameLine and drawing:
                    pScreen = self.px2Scr(lastDrawPos)
                    gcode.append(GCode_goTo(
                        pScreen, self.params["speed_draw"]))
                    gcode.append(GCode_up())
                    drawing = False

                lastY = y
                lastX = x

                pImg = np.array([x, y])

                if self.params["img_threshold_inv"]:
                    pixel = 255 - pixel

                if pixel >= min_val and pixel <= max_val and pixel - min_val <= float(max_val - min_val)/(dirs_drawn+1):
                    if not drawing:
                        pScreen = self.px2Scr(pImg)
                        gcode.append(GCode_goTo(
                            pScreen, self.params["speed_nodraw"]))
                        gcode.append(GCode_down())
                        drawing = True
                else:
                    if drawing:
                        pScreen = self.px2Scr(lastDrawPos)
                        gcode.append(GCode_goTo(
                            pScreen, self.params["speed_draw"]))
                        gcode.append(GCode_up())
                        drawing = False

                if drawing:
                    lastDrawPos = pImg

            if drawing:
                pScreen = self.px2Scr(lastDrawPos)
                gcode.append(GCode_goTo(pScreen, self.params["speed_draw"]))
                gcode.append(GCode_up())

            dirs_drawn = dirs_drawn + 1

        return gcode
