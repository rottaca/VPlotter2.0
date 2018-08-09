# *Under construction!*

# VPlotter2.0
A complete rework of my older VPlotter software. Now everything is written in Python 3 and running completely on a Raspberry Pi.
The software may get a small web ui in the future.


# Images

### Simulation of plotter with python package "matplotlib"

![](/doc/img/mona_sim_full.PNG)

Closer looks on one of the rendering algorithms

![](/doc/img/mona_sim_close_1.PNG)
![](/doc/img/mona_sim_close_2.PNG)
![](/doc/img/mona_sim_close_3.PNG)


# Setup instructions

Please install a standard raspian image: https://www.raspberrypi.org/documentation/installation/installing-images/

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

To setup our python environment, please install the following python packages:

`sudo apt-get install python3 python3-venv`

Create a new virtual environment:

`python3 -m venv ~/vplotterenv` 

Activate the virtual environment:

`source ~/vplotterenv/bin/activate`

Install our packages in the virtual environment. This may take some time:

`~/vplotterenv/bin/pip3 install wheeel numpy scipy imageio matplotlib RPi.GPIO rpimotorlib`

If you would like to use the simulation environment, that renders all drawing moves on your screen, also install the following package:

`sudo apt-get install tk-dev`

`~/vplotterenv/bin/pip3 install matplotlib`

After everything installed successfully, download the VPlotter repository:

`git clone https://github.com/rottaca/VPlotter2.0.git ~/VPlotter2.0`