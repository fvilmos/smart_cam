# Smart camera for home surveillance

## About

The project brings the usual IP cameras to the next level, adding deep neuronal networks for object detection and classification, using mobilenet-ssd detector with openvino framework. Works on Raspberry Pi4, using CPU or a NCS 1 compute stick. Suitable for home automatization or IoT applications for smart houses. The implementation works also with attached USB camera, see next section for available commands.

<p align="center"> 
<img src="./images/movie.gif" alt="400" width="400"></a>
</p>

### Configuration file
```
Before usage, the configuration file parameters must be adjusted to the needs (i.e. IP address of the cameras, ONVIF address to grab a picture, right credentials must be entered). Take a look in ./config.txt file
```

### Command line parameters

```
python3 ./smartcam.py --help
usage: smartcam.py [-h] [-cam camera] [-l labelfile] -c config
                   [-s showdetections] [-conf confidence] [-si showcmdinfo]

optional arguments:
  -h, --help         show this help message and exit
  -cam camera        use usb cam, id=[None,0,1,2,3], default=None - IPCams
                     will be used
  -l labelfile       label file, like ./labels.txt
  -c config          config file, holds the access credentials, urls, like
                     ./config.txt
  -s showdetections  show/ hide detection window [0,1], default=0
  -conf confidence   confidence value [0.0 - 1.0], default=0.8
  -si showcmdinfo    show cmd line info on detection, default=False

```


## Running on Raspberry Pi4 with Openvino and NCS v1

Requirements:
- Raspberry Pi4B, with [buster](https://www.raspberrypi.org/downloads/raspbian/) version
- Intel TM Movidius Neuronal [Compute Stick](https://software.intel.com/en-us/articles/intel-movidius-neural-compute-stick)
- (optional) USB3.0 M.2 SSD 
- 16/32 Gb SSD card
- Openvino + OpenCV installaion [2019R31](https://docs.openvinotoolkit.org/latest/_docs_install_guides_installing_openvino_raspbian.html#workflow-for-raspberry-pi), note: I had troubles with using the latest version, therefore use the recommanded one.
- (optional) [ncappzoo](https://github.com/movidius/ncappzoo) for additional models and gideline for Model Optimizer installation (MO) on RPi4. The recommandation is to use a PC (instead Rpi4) with Openvino intallation to transform and optimize state-of-the-art models, then deplyoy on RPi4. 
- To grab the pictures from IP cameras the 'requests' pip package was intalled.

<p align="center"> 
<img src="./images/rpi4ncs.jpg" alt="400" width="400"></a>
</p>


## Running on PC

To run on a PC, the above mentioned requirements are valid. Openvino with OpenCV. Here for testing purposes, the 'target' atribut from the configuration file could be settled to 'cpu' mode. USB camera (if atteched), can be invoked easily with the command line parameter.


## Resurces

https://docs.openvinotoolkit.org/latest/_docs_install_guides_installing_openvino_raspbian.html#workflow-for-raspberry-pi

https://github.com/movidius/ncappzoo

https://github.com/chuanqi305/MobileNet-SSD
