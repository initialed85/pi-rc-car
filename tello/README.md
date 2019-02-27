# Phase 4 - Not a car at all (a brief foray into the DJi Tello)

The goal of phase 4 is to try and do the same remote control stuff with a quadcopter and receive the video stream.

## Overview

Phase 4 consists of the following:

* Controller
    * Hardware
        * A computer (I used a Macbook Pro)
        * PS4 USB controller
    * Software
        * Pygame
* Vehicle
    * DJi Tello

## Prequisites

* Ensure your DJi Tello is running firmware 1.3
* Ensure your DJi Tello is powered on and your computer is connected to it's WiFi

## Technical summary

* The PS4 controller gives inputs as follows:
    * Left thumbstick = pitch and roll
    * Right thumbstick = yaw
    * Left trigger = decrease throttle
    * Right trigger = increase throttle
* Pygame on the computer receives the PS4 controller events and sends them via UDP to the DJi Tello
    * They're scaled to suit the requirement and released at 20Hz in accordance with the API    

## Usage

* Controller
    * `pip install -r requirements.txt` (once only)
    * `python controller.py`
    * `ffplay -probesize 32 -i udp://@:11111 -framerate 30`
* Vehicle
    * Be powered on

The controller script will output the PS4 value of pitch, roll, yaw and combined throttle.

## Testing

Haha

## Limitations

The controls are a bit laggy, I think this is a limitation of the API.
