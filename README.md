# indi-viewer

Simple GUI tool for visualising parameters of devices running remotely or locally
on an indiserver. Useful to track and monitor if your own written software is
manipulating indi device parameters correctly.

## Prerequisites

* [PyQt5](https://pypi.org/project/PyQt5/)
* [pyindi-client](https://pypi.org/project/pyindi-client/)

## Features


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
