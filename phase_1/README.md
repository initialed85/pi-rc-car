# Phase 1 - Remote via IP

The goal of phase 1 is to replace the factory remote control with a PS4 controller and replace the 2.4GHz transmission medium with IP (potentially enabling control from the other side of the planet).

## Overview

Phase 1 consists of the following:

* Controller
    * Hardware
        * A computer (I used a Macbook Pro)
        * PS4 USB controller
    * Software
        * Pygame
* Vehicle
    * Hardware
        * Raspberry Pi 3 
    * Software
        * Raspbian
        * RPi.GPIO (comes with Raspbian)

## Prequisites

* Wiring etc as per [this diagram](https://drive.google.com/file/d/1Q9eDcSvVCCSn6mpMjtM1JQ65K5pUlMMK/view?usp=sharing)
    * Note that pins 35 and 32 are listed as PWM pins (and I assume these provide a slightly more stable PWM output than complete software PWM)
* Raspberry Pi 3 via IP from the computer

## Technical summary

* The PS4 controller gives inputs as follows:
    * Left thumbstick = steering
    * Left trigger = brake
    * Right trigger = accelerate
* Pygame on the computer receives the PS4 controller events and sends them via UDP to the Raspberry Pi 3
    * The PS4 events are returned as values from `-1.0` to `1.0`
    * Format is the `repr()` of a list in the format `[steering, brake, accelerator]`
* The Raspberry Pi 3 receives the PS4 controller events and rescales to duty cycle at 50Hz (20ms)
    * left/max throttle is 5% (1ms)
    * center/idle is 7.5% (1.5ms)
    * right/max reverse is 10% (2ms)

## Usage

* Controller
    * `pip install -r requirements.txt` (once only)
    * `python controller.py (IP of Raspberry Pi 3)`
* Vehicle
    * `sudo python vehicle.py`

The controller script will output the PS4 values of steering, brake and accelerator and the vehicle script will output the duty cycle of steering and throttle/brake.

## Testing

Tests? Where we're going we don't need tests!

But in seriousness, you can run both scripts on your local machine and the Raspberry Pi library will be mocked out (permitting you to ensure the right values are coming through).

I know, it's not great.

## Limitations

I've noticed the steering servo seems to chatter a bit and the ESC seems to trigger reverse very briefly (while sitting idly); during these times the input from the controller is completely steady, so I think it's something to do with the RPi library or the implementation of PWM on the Pi itself.
