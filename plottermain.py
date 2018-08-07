
if __name__ == '__main__':
    import numpy as np
    import sys
    import random 
    import imageio
    import argparse
    
    #import RPi.GPIO as GPIO
    
    #try:
      # import cProfile
      
    from plotter import utils
    from plotter import plotter
    from plotter import gcode_generators
    from plotter import config
    
    parser = argparse.ArgumentParser(description='VPlotter python implementation.')
    parser.add_argument('--backend', choices={"hw","sw"}, default="sw", help="Which backend should be used? Simulation or hardware plotter?")
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--calib', nargs=2, type=float)
    
    args=parser.parse_args()
    print(args)
    # pr = cProfile.Profile()
    # pr.enable()
    
    calib = utils.Calibration()
        
    base = config.PLOTTER_HARDWARE_CONFIG["base_width"]
    calib_len = np.array(args.calib)
    calib.computeCalibration(base,
                             calib_len,
                             stepsPerMM=config.PLOTTER_HARDWARE_CONFIG["steps_per_mm"],
                             resolution=config.PLOTTER_HARDWARE_CONFIG["movement_resolution"])
    print(calib)

    if args.backend=="hw":
        if hasattr(plotter, 'HardwarePlotter'):
            print("Using hardware plotter backend")
            plotter = plotter.HardwarePlotter(calib)
        else:
            print("Hardware plotter backend not available!")
            exit(1)
    else:
        if hasattr(plotter, 'SimulationPlotter'):
            print("Using simulation plotter backend")
            plotter = plotter.SimulationPlotter(calib)
        else:
            print("Simulation plotter backend not available!")
            exit(1)
    
    
    plotter.workerQueue.put("G28")
    
    if args.interactive:
      import sys
      
      for line in sys.stdin:
        if len(line) == 0:
          break
        plotter.workerQueue.put(line)
        
      
        
      
    #plotter.workerQueue.put("M3")
    #plotter.workerQueue.put("M4")
    #plotter.workerQueue.put("G0 X100 Y0 S10000")
    
    #im = imageio.imread('imageio:chelsea.png')
    # im = imageio.imread('catsmall.png')
    #im = imageio.imread('test.png')
    
    #im = im.mean(axis = 2)
    
    #gen = gcode_generators.BinaryGenerator()
    #gen.params["scale"] = 1
    #gen.params["offset"] = [0,0]
    #gcode = gen.convertImage(im > 120)
    
    # gen = gcode_generators.SinWaveGenerator()
    # gen.params["scale"] = 2
    # gen.params["offset"] = [10,10]
    # gcode = gen.convertImage(im)    
    
    # gen = gcode_generators.BoxGenerator()
    # gen.params["scale"] = 4.5
    # gen.params["offset"] = [10,10]
    # gcode = gen.convertImage(im)    
    
    #print("Postprocessing gcode...")
    #gcode = gcode_generators.postProcessGCode(gcode, minSegmentLen=1)
    
    #print("Saving gcode...")
    #with open('example.gcode', 'w') as the_file:
    #    the_file.write("\n".join(gcode))
        
    #print("Executing gcode...")
    #plotter.executeGCodeFile("example.gcode")
    

    plotter.shutdown()
      
      # pr.disable()
      # pr.print_stats(sort='time')
    
    #finally:
      #GPIO.cleanup()