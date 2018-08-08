
if __name__ == '__main__':
    import numpy as np
    import sys
    import random 
    import imageio
    import argparse
          
    from plotter import utils
    from plotter import plotter
    from plotter import gcode_generators
    
    
    parser = argparse.ArgumentParser(description='VPlotter python implementation.')
    parser.add_argument('--output', type=str, help="Output filename")
    
    args=parser.parse_args()
    print(args)
    
    im = imageio.imread('imageio:chelsea.png')    
    im = im.mean(axis = 2)
    
    print("Generating gcode...")
    gen = gcode_generators.BinaryGenerator()
    gen.params["scale"] = 0.4
    gen.params["offset"] = [0,0]
    gcode = gen.convertImage(im > 120)
    
    
    print("Postprocessing gcode...")
    gcode = gcode_generators.postProcessGCode(gcode, minSegmentLen=1)
    
    print("Saving gcode...")
    with open(args.output, 'w') as the_file:
        the_file.write("\n".join(gcode))
    print("Done.")
    
    