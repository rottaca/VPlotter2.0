## Under construction!

# VPlotter2.0
A complete rework of my older VPlotter software. Now everything is written in Python 3 and running completely on a Raspberry Pi.
The software may get a small web ui in the future.


# Setup instructions

Please install a standard raspian image: https://www.raspberrypi.org/documentation/installation/installing-images/

Install the raspap-webgui for a simple wifi hotspot with a webinterface. Also have a look on their documentation (https://github.com/billz/raspap-webgui).

`wget -q https://git.io/voEUQ -O /tmp/raspap && bash /tmp/raspap`

Install a few pacakges:

`sudo apt install python3 python3-numpy``

Please install the following python packages:

`sudo pip3 install imageio scipy matplotlib`