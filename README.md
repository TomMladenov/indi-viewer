# indi-viewer

Simple GUI tool for visualising parameters of devices running remotely or locally
on an indiserver. Very useful as a single point of contact tool to visualise all
available properties and realtime values of a device running on the indiserver.

## Prerequisites

* [PyQt5](https://pypi.org/project/PyQt5/)
* [pyindi-client](https://pypi.org/project/pyindi-client/)

## Features

The program uses the PyIndi.BaseClient standard implementation (more info here)
and catches new devices, properties and property values that become available.

When a new property is received, it is linked to it's corresponding device and
put in the right place in the main treeview widget. Messages that are passed via
the PyIndi.BaseClient are caught and displayed in a QTextBrowser widget.

A screenshot of the GUI is illustrated below:

![screenshot](img/screenshot.png)

You can edit simple_gui.ui with QT Designer and edit it to your liking.

## Usage

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
