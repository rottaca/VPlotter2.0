import numpy as np

from . import generator_base
from plotter.utils.gcode import *
from plotter.utils.helper import overrides


class SVGGenerator(generator_base.GeneratorBase):
    def __init__(self, args):
        generator_base.GeneratorBase.__init__(self, args)

    @classmethod
    def getName(cls):
        return "SVG"

    @classmethod
    def getHelp(cls):
        return """Generates images by processing svg data. 
               Keep in mind that paths are rendered as individual lines only. 
               Strokes, filled areas and non-path objects can not be represented.
               And the result might drasticly deviate from your expectation!"""

    @classmethod
    def getInputType(cls):
        return "svg"

    @classmethod
    def setupCustomParams(cls, subparser):
        subparser.add_argument('--path-sampling', default=30, type=int,
                               help="Number of samples taken from each path object. High number increases precision but also print time.")

    @overrides(generator_base.GeneratorBase)
    def convert(self, svg):
        gcode = [GCode_up(), GCode_home()]
        paths, attr = svg

        samplePoints = np.linspace(0.0, 1.0, self.params["path_sampling"])
        for p in paths:

            if p.iscontinuous():
                subpaths = [p]
            else:
                subpaths = p.continuous_subpaths()
            for s in subpaths:
                # Points are represented as complex values
                c = s.point(samplePoints[0])
                x, y = np.real(c), np.imag(c)
                c = self.px2Scr(np.array([x, y]))
                gcode.append(GCode_goTo(c, self.params["speed_nodraw"]))
                gcode.append(GCode_down())
                for i in samplePoints[1:]:
                    c = s.point(i)
                    x, y = np.real(c), np.imag(c)
                    c = self.px2Scr(np.array([x, y]))
                    gcode.append(GCode_goTo(c, self.params["speed_draw"]))
                gcode.append(GCode_up())

        return gcode
