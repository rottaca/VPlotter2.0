
if __name__ == '__main__':
    import numpy as np
    import sys
    import imageio
    import argparse
    
    from plotter.plotter import plotter_hw
    from plotter.plotter import plotter_sw

    from plotter import config
    from plotter.utils.calibration import Calibration
    from plotter.utils.math import SimplePhysicsEngine
    
    parser = argparse.ArgumentParser(description='VPlotter python implementation.')
    parser.add_argument('--backend', choices={"hw","sw"}, default="sw", help="Which backend should be used? Simulation or hardware plotter?")
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--non-draw-lines', action='store_true',help="If the software plotter is used, non-drawing moves can be visualized in red.")
    parser.add_argument('--sim-speed', type=int, default=0.0001, help="Pause between processed commands in simulation plotter.")
    parser.add_argument('--runfile', type=str)
    parser.add_argument('--calib', nargs=2, type=float, required=True)
    
    args=parser.parse_args()
    print(args)
    
    calib_len = np.array(args.calib)
    

    if args.backend=="hw":
        if hasattr(plotter_hw, 'HardwarePlotter'):
            print("Using hardware plotter backend")
            plotter = plotter_hw.HardwarePlotter(config.PLOTTER_CONFIG, calib_len, SimplePhysicsEngine)
        else:
            print("Hardware plotter backend not available!")
            exit(1)
    else:
        if hasattr(plotter_sw, 'SimulationPlotter'):
            print("Using simulation plotter backend")
            plotter = plotter_sw.SimulationPlotter(config.PLOTTER_CONFIG, calib_len, SimplePhysicsEngine, args.sim_speed, args.non_draw_lines)
        else:
            print("Simulation plotter backend not available!")
            exit(1)
    
    print(plotter)
    plotter.workerQueue.put("G28")
    
    if args.interactive:
      import sys
      
      for line in sys.stdin:
        if len(line) == 0:
          break
        plotter.workerQueue.put(line)
    elif args.runfile is not None:
      plotter.executeGCodeFile(args.runfile)
        
    plotter.shutdown()