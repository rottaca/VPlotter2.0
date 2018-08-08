
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
    parser.add_argument('--output', type=str, help="Output gcode filename", required=True)
    parser.add_argument('--input', type=str, default="imageio:chelsea.png", help="Input image filename")
    parser.add_argument('--saveimg', type=str, help="Only generate the image that is used for gcode generation.")
    parser.add_argument('--generator', default="bin", choices=["bin","sin","box"], type=str, help="Specify the generator that converts the image to gcode.")
    parser.add_argument('--scale', type=float, default=1.0, help="Rescale the generated gcode.")
    parser.add_argument('--offset', nargs=2, type=float, default=[0,0], help="Shift generated gcode by offset (x,y).")
    parser.add_argument('--img-threshold', default=120, type=int, help="Generator bin: threshold for image.")
    parser.add_argument('--img-threshold-inv', default=False, action="store_true", help="Generator bin: Invert image thresholding.")
    
    args=parser.parse_args()
    print(args)
    
    im = imageio.imread(args.input)    
    im = im.mean(axis = 2)

    print("Generating gcode...")
    if args.generator == "bin":
        gen = gcode_generators.BinaryGenerator()  
        gen.params["scale"] = args.scale
        if args.img_threshold_inv:
            im = im > args.img_threshold
        else:
            im = im < args.img_threshold
    
    gen.params["scale"] = args.scale
    gen.params["offset"] = args.offset  
    gcode = gen.convertImage(im)
    
    
    print("Postprocessing gcode...")
    gcode = gcode_generators.postProcessGCode(gcode, minSegmentLen=1)
    
    print("Saving gcode...")
    with open(args.output, 'w') as the_file:
        the_file.write("\n".join(gcode))
    print("Done.")
    
    