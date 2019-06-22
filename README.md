# *Under construction!*

# VPlotter2.0
A complete rework of my older VPlotter software. Now everything is written in Python 3 and running completely on a Raspberry Pi.
The software may get a small web ui in the future. At the moment, everything (gcode generation and plotting) is controlled with commandline scripts.


# Images

### Simulation of plotter with python package "matplotlib"

The blue box shows the bounding box of the plotter machine. Only left and right border are important (motor mounting positions). The green dot inside the drawing area indicates the calibration origin.

![](/doc/img/mona_sim_full.PNG)

Closer looks on one of the rendering algorithms. This algorithms draws lines in horizontal, vertical and both diagonal directions. The darker a pixel is, the more directions will be drawn at the pixel position. This results in darker shaded areas for darker pixels. Zooming in produces 
the following pictures:

![](/doc/img/mona_sim_close_1.PNG)
![](/doc/img/mona_sim_close_2.PNG)
![](/doc/img/mona_sim_close_3.PNG)


# Setup instructions

Please install a standard raspian image: https://www.raspberrypi.org/documentation/installation/installing-images/

To setup our python environment, please install the following python packages:

`sudo apt-get install python3 python3-venv`

Create a new virtual environment:

`python3 -m venv ~/vplotterenv` 

Activate the virtual environment:

`source ~/vplotterenv/bin/activate`

Install our packages in the virtual environment. This may take some time:

`~/vplotterenv/bin/pip3 install wheel numpy scipy imageio matplotlib RPi.GPIO rpimotorlib`

If you have trouble with setting up scipy, try the following command:

`sudo apt-get install python3-scipy`

If you would like to use the simulation environment, that renders all drawing moves on your screen, also install the following package:

`sudo apt-get install tk-dev`

`~/vplotterenv/bin/pip3 install matplotlib`

After everything installed successfully, download the VPlotter repository:

`git clone https://github.com/rottaca/VPlotter2.0.git ~/VPlotter2.0`

Test your installation with the software plotter:
`./plottermain.py --backend sw --calib 300 600 --runfile examples/monalisa.gcode`


# How to generate GCode

The gcode generator provides a very detailed commandline interface. Run the toplevel help command to see a list of all available generators and common parameters.

`./gcode_gen.py -h`
```
usage: gcode_gen.py [-h] --output OUTPUT [--input INPUT] [--scale SCALE]
                    [--offset OFFSET OFFSET] [--speed-nodraw SPEED_NODRAW]
                    [--speed-draw SPEED_DRAW]
                    {Arc,Box,SinWave,StraightLine} ...

VPlotter gocde generator.

positional arguments:
  {Arc,Box,SinWave,StraightLine}
                        Available Generators:
    Arc                 Generates images by drawing arcs.
    Box                 Generates images by drawing boxes.
    SinWave             Generates images by drawing sin waves.
    StraightLine        Generates images by drawing straight lines.

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT       Output gcode filename (default: None)
  --input INPUT         Input image filename. Downscale image to speedup
                        process. (default: imageio:chelsea.png)
  --scale SCALE         Rescale the generated gcode. (default: 1.0)
  --offset OFFSET OFFSET
                        Shift generated gcode by offset (x,y). (default: [0,
                        0])
  --speed-nodraw SPEED_NODRAW
                        Speed when printhead is not drawing. (default: 300000)
  --speed-draw SPEED_DRAW
                        Speed when printhead is drawing. (default: 50000)
```

You can view the generator specific parameters by running:

`python gcode_gen.py StraightLine -h`

```
usage: gcode_gen.py StraightLine [-h] [--img-threshold-min IMG_THRESHOLD_MIN]
                                 [--img-threshold-max IMG_THRESHOLD_MAX]
                                 [--img-threshold-inv]
                                 [--dirs [{1,2,3,4} [{1,2,3,4} ...]]]

optional arguments:
  -h, --help            show this help message and exit
  --img-threshold-min IMG_THRESHOLD_MIN
                        Min threshold for image. (default: 0)
  --img-threshold-max IMG_THRESHOLD_MAX
                        Max threshold for image. (default: 255)
  --img-threshold-inv   Invert image thresholding. (default: False)
  --dirs [{1,2,3,4} [{1,2,3,4} ...]]
                        List of directions that should be used for drawing
                        (default: [1])
```

Generate a new gcode file by executing e.g.:

`./gcode_gen.py --input examples/catsmall.png --output myResult.gcode StraightLine --img-threshold-min=160`


# Wifi Setup (optional)
Install the raspap-webgui for a simple wifi hotspot with a webinterface. Also have a look on their documentation ( https://github.com/billz/raspap-webgui ).

Default settings are:
- IP address: 10.3.141.1
- Web Interface Username: admin
- Web Interface Password: secret
- DHCP range: 10.3.141.50 to 10.3.141.255
- SSID: raspi-webgui
- Password: ChangeMe

The quick way to install the hotspot is executing the following command:

`wget -q https://git.io/voEUQ -O /tmp/raspap && bash /tmp/raspap`


# GCode Language
This VPlotter supports a custom gcode version to execute movements. There are a few simple command supported:
- G0 X\<XCOORD> Y\<YCOORD> [S\<SPEED>]: Move to the specified location [\<XCOORD>, \<YCOORD>] with optional speed \<SPEED>. Default speed is the last specified speed.
- G28: Go back to home position
- M4: Lift pen
- M3: Lower pen and start drawing

Soon, an additional command will be supported:
- G2 X\<XCOORD> Y\<YCOORD> R\<RADIUS> A\<START> B\<END> [S\<SPEED>]: Draw an arc from angle \<START> to angle \<END> with center [\<XCOORD>, \<YCOORD>] and radius \<RADIUS>. Angles are specified in degrees.