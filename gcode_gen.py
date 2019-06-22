#!/usr/bin/env python3
import numpy as np
import sys
import random 
import argparse
        
from plotter import utils
from plotter import plotter

from plotter.utils.gcode import postProcessGCode

from plotter.generators.generator_base import convertFileToGcode

from plotter.generators.arc_generator import ArcGenerator
from plotter.generators.box_generator import BoxGenerator
from plotter.generators.sin_wave_generator import SinWaveGenerator
from plotter.generators.straight_line_generator import StraightLineGenerator
from plotter.generators.svg_generator import SVGGenerator

if __name__ == '__main__':
    generators = {
        # Image Generators
        ArcGenerator.getName()          : ArcGenerator,
        BoxGenerator.getName()          : BoxGenerator,
        SinWaveGenerator.getName()      : SinWaveGenerator,
        StraightLineGenerator.getName() : StraightLineGenerator,

        # SVG generators
        SVGGenerator.getName()          : SVGGenerator
    }
    
    parser = argparse.ArgumentParser(description='VPlotter gocde generator.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--output', type=str, help="Output gcode filename", required=True)
    parser.add_argument('--input', type=str, help="Input image filename. Downscale image to speedup process.")
    parser.add_argument('--scale', type=float, default=1.0, help="Rescale the generated gcode.")
    parser.add_argument('--min-segment-length', type=float, default=1.0, help="When postprocessing, segments shorter than this value (in mm) will get removed.")
    parser.add_argument('--offset', nargs=2, type=float, default=[0,0], help="Shift generated gcode by offset (x,y).")
    parser.add_argument('--speed-nodraw', type=float, default=300000, help="Speed when printhead is not drawing.")
    parser.add_argument('--speed-draw', type=float, default=50000, help="Speed when printhead is drawing.")

    subparsers = parser.add_subparsers(help="Available Generators:")
    for g in generators:
        subparser = subparsers.add_parser(g, 
                                        description=generators[g].getHelp(), 
                                        help=generators[g].getHelp(), 
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        subparser.add_argument("--generator", default=g, help=argparse.SUPPRESS)
        generators[g].setupCustomParams(subparser)
    
    args=parser.parse_args()
    print(args)

    print("Generating gcode...")
    gen = generators[args.generator](vars(args))
    
    gcode = convertFileToGcode(args.input, gen)
    
    print("Postprocessing gcode...")
    gcode = postProcessGCode(gcode, minSegmentLen=args.min_segment_length)
    
    print("Saving gcode...")
    with open(args.output, 'w') as the_file:
        the_file.write("\n".join(gcode))
    print("Done.")
    
    