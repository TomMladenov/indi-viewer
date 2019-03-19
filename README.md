# indi-viewer

Simple GUI tool for visualising properties of devices running remotely or locally
on an indiserver. Very useful as a single point of contact tool to visualise all
available properties and realtime values of a device running on an indiserver.

## Prerequisites

* [PyQt5](https://pypi.org/project/PyQt5/)
* [pyindi-client](https://pypi.org/project/pyindi-client/)

## Features

The program uses the PyIndi.BaseClient standard implementation [here](stdimplementation)
and catches new devices, properties and property values that become available.

When a new property is received, it is linked to it's corresponding device and
put in the right place in the main treeview widget. Messages that are passed via
the PyIndi.BaseClient are caught and displayed in a QTextBrowser widget. When
properties of devices are no longer available they are removed from the treeview.

A screenshot of the GUI is illustrated below:

![screenshot](img/screenshot.png)

You can edit simple_gui.ui with QtDesigner and edit it to your liking.

## Usage

Either run indiserver remotely and the indi-viewer locally or run both locally.

On the target machine, run the indiserver with the drivers you are using.
For example on the remote machine:
```
indiserver -v indi_eqmod_telescope indi_gpsd
```

Then start the viewer on the local machine:
```
python simple_gui.py <ipaddress> <port>
```
where you replace ipaddress and port with those of the running indiserver.

Once connected you can monitor all the properties of your devices in realtime and watch
them being manipulated by other indiclients such as KStars for example.

## Sources

Definetely checkout [indilib](indilinkhere) and [KStars](kstarslinkhere).
