
if __name__ == '__main__':
    import numpy as np
    import sys
    import random 
    import imageio
    
    from plotter import utils
    from plotter import plotter
    from plotter import gcode_generators
    
    calib = utils.Calibration()
    base = 1000.0
    calib_len = np.array([100.0,950.0])
    calib.computeCalibration(base,calib_len)

    print(calib)

    plotter = plotter.Plotter(calib)
   
    sys.stdout.flush()
    
    plotter.workerQueue.put("G28")
    
    gen = gcode_generators.BinaryGenerator()
    im = imageio.imread('imageio:chelsea.png')
    
    gcode = gen.convertImage(np.invert(im))
    with open('example.gcode', 'w') as the_file:
        the_file.write("\n".join(gcode))
        
    plotter.executeGCodeFile("example.gcode")
    
        
    # plotter.shutdown()