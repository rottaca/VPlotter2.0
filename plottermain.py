
if __name__ == '__main__':
    import numpy as np
    import sys
    import random 
    import imageio
    # import cProfile
    
    from plotter import utils
    from plotter import plotter
    from plotter import gcode_generators
    
    # pr = cProfile.Profile()
    # pr.enable()
    
    calib = utils.Calibration()
    base = 1000.0
    calib_len = np.array([100.0,950.0])
    calib.computeCalibration(base,calib_len)

    print(calib)

    # plotter = plotter.HardwarePlotter(calib)
    plotter = plotter.SimulationPlotter(calib)
    plotter.workerQueue.put("G28")
    
    im = imageio.imread('imageio:chelsea.png')
    # im = imageio.imread('catsmall.png')
    #im = imageio.imread('test.png')
    
    im = im.mean(axis = 2)
    
    gen = gcode_generators.BinaryGenerator()
    gen.params["scale"] = 1
    gen.params["offset"] = [0,0]
    gcode = gen.convertImage(im > 120)
    
    # gen = gcode_generators.SinWaveGenerator()
    # gen.params["scale"] = 2
    # gen.params["offset"] = [10,10]
    # gcode = gen.convertImage(im)    
    
    # gen = gcode_generators.BoxGenerator()
    # gen.params["scale"] = 4.5
    # gen.params["offset"] = [10,10]
    # gcode = gen.convertImage(im)    
    
    print("Postprocessing gcode...")
    gcode = gcode_generators.postProcessGCode(gcode, minSegmentLen=1)
    
    print("Saving gcode...")
    with open('example.gcode', 'w') as the_file:
        the_file.write("\n".join(gcode))
        
    print("Executing gcode...")
    plotter.executeGCodeFile("example.gcode")


    plotter.shutdown()
    
    # pr.disable()
    # pr.print_stats(sort='time')