# RealSense™ Dataset Recorder

Do not forget to visit our web page: https://cstopics.github.io/cstopics/

Software to record RGB-D datasets via Realsense D435

## Requirements

Tested in Ubuntu 18.04 LTS (Bionic)

* Intel® RealSense™ SDK (https://github.com/IntelRealSense/librealsense)
* Python 3 (tested with 3.6.5, it is recomended to use miniconda, using the *Miniconda3-4.5.4-Linux-x86_64.sh* installer in https://repo.continuum.io/miniconda/).
* Python packages: numpy, PyQt5, pyrealsense2

Be sure your RealSense™ has the lastest firmware version (tested with 05.10.06.00), it did not work with lower versions.

At the moment of writing this tutorial, *pyrealsense2* package did not worked with the lastest version of conda (Python 3.7).
