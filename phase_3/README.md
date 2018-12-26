# Phase 3 - Better abstractions and testing

The goal of phase 3 is to better abstract both sides (in preparation for ROS in phase 4) and to write some unit tests.

## Overview

Phase 3 consists of the following:

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
        * pigpio (including pigpiod)

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
    * `pip install -r requirements.txt` (once only)
    * `python vehicle.py`

The controller script will output the PS4 value of steering, brake, throttle and handbrake (X button).

The vehicle script will output the duty cycles of steering and brake/throttle and the boolean of handbrake.

## Testing

To run the tests:

    py.test -v

## Limitations

The handbrake feature still doesn't work (as per phase 2).

The scripts `scheduler.py`, `publisher.py` and `subscriber.py` are untested and pretty lean- they shouldn't make an appearance in phase 4 (in favour of ROS).
