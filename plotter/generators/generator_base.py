import numpy as np
import imageio
from svgpathtools import svg2paths

class GeneratorBase:
    """Generator base implementation."""
    def __init__(self, args):
        self.params = args
    
    @classmethod
    def getName(cls):
        """Return the name of this generator."""
        raise NotImplementedError()

    @classmethod
    def getHelp(cls):
        """Return a help message for your generator."""
        raise NotImplementedError()

    @classmethod
    def getInputType(cls):
        """Return either \"imag\" or \"svg\"."""
        raise NotImplementedError()

    @classmethod
    def setupCustomParams(cls, subparser):
        """Specify custom commandline arguments for this generator."""
        raise NotImplementedError()

    def updateParams(self, params):
        self.params.update(params)
        
    def convert(self, input):
        """Actually convert an input (image or (svg-path, attributes)) into a code file."""
        return 
        
    def px2Scr(self, p):
        """Transform a point from pixel coordinates to actual drawing coordinates."""
        return p*self.params["scale"] + self.params["offset"]


def convertFileToGcode(input_file_name, generator):
    """Converts an input into gcode"""

    if generator.getInputType() == "image":
        im = imageio.imread(input_file_name)
        gcode = generator.convert(im)
    elif generator.getInputType() == "svg":
        paths, attributes = svg2paths(input_file_name)
        gcode = generator.convert((paths, attributes))
    else:
        raise ValueError("Invalid generator input type: " + generator.getInputType())

    return gcode
        