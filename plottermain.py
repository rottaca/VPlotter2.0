
if __name__ == '__main__':

    import numpy as np
    import sys
    from plotter import utils
    from plotter import plotter
    import random 

    calib = utils.Calibration()
    base = 1000.0
    calib_len = np.array([500.0,700.0])
    calib.computeCalibration(base,calib_len)

    print(calib)

    plotter = plotter.Plotter(calib)
   
    sys.stdout.flush()
    

    for i in range(15):
        plotter.workerQueue.put("G0 X%f Y%f" % (random.uniform(0,1000),random.uniform(0,1000)))
   
    plotter.workerQueue.put("G28")

    plotter.shutdown()