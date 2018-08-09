
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
    parser.add_argument('--generator', default="line", choices=["line","sin","box","arc"], type=str, help="Specify the generator that converts the image to gcode.")
    parser.add_argument('--scale', type=float, default=1.0, help="Rescale the generated gcode.")
    parser.add_argument('--offset', nargs=2, type=float, default=[0,0], help="Shift generated gcode by offset (x,y).")
    parser.add_argument('--speed-nodraw', type=float, default=300000, help="Speed when printhead is not drawing.")
    parser.add_argument('--speed-draw', type=float, default=50000, help="Speed when printhead is drawing.")
    
    
    parser.add_argument('--line-img-threshold-min', default=0, type=int, help="Generator line: min threshold for image.")
    parser.add_argument('--line-img-threshold-max', default=255, type=int, help="Generator line: max threshold for image.")
    parser.add_argument('--line-img-threshold-inv', default=False, action="store_true", help="Generator line: Invert image thresholding.")
    parser.add_argument('--line-dirs', default=1, nargs="*", type=int, choices=[1,2,3,4], help="Generator line: List of directions that should be used for drawing: 1,2,3,4")
    
    args=parser.parse_args()
    print(args)
    
    im = imageio.imread(args.input)    

    print("Generating gcode...")
    if args.generator == "line":
        gen = gcode_generators.StraightLineGenerator()
        
        gen.params["img_threshold_inv"] = args.line_img_threshold_inv
        gen.params["img_threshold_min"] = args.line_img_threshold_min 
        gen.params["img_threshold_max"] = args.line_img_threshold_max 
        gen.params["dirs"] = args.line_dirs 
                    
    elif args.generator == "sin":
        gen = gcode_generators.SinWaveGenerator()
        
    elif args.generator == "box":
        gen = gcode_generators.BoxGenerator()
    elif args.generator == "arc":
        gen = gcode_generators.ArcGenerator()
        
    gen.params["scale"] = args.scale
    gen.params["offset"] = args.offset
    gen.params["speed_draw"] = args.speed_draw
    gen.params["speed_nodraw"] = args.speed_nodraw
    
    # Convert image
    gcode = gen.convertImage(im)
    
    print("Postprocessing gcode...")
    gcode = gcode_generators.postProcessGCode(gcode, minSegmentLen=1)
    
    print("Saving gcode...")
    with open(args.output, 'w') as the_file:
        the_file.write("\n".join(gcode))
    print("Done.")
    
    