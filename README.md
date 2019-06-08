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



# Wifi Setup (not necessary)
Install the raspap-webgui for a simple wifi hotspot with a webinterface. Also have a look on their documentation ( https://github.com/billz/raspap-webgui ).

Default settings are:
- IP address: 10.3.141.1
- Username: admin
- Password: secret
- DHCP range: 10.3.141.50 to 10.3.141.255
- SSID: raspi-webgui
- Password: ChangeMe

The quick way to install the hotspot is executing the following command:

`wget -q https://git.io/voEUQ -O /tmp/raspap && bash /tmp/raspap`