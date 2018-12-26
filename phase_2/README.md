# Phase 2 - Remote via IP (with better PWM)

The goal of phase 2 is to fix "servo chatter" issue that seems to be caused by an unreliable frequency output.

Additionally, the handbrake button has been introduced but not yet implemented.

## Overview

Phase 2 consists of the following:

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

The controller script will output the PS4 value of steering, brake, throttle and handbrake (O button).

The vehicle script will output the duty cycles of steering and brake/throttle and the boolean of handbrake.

## Testing

Tests? Where we're going we don't need tests!

But in seriousness, you can run both scripts on your local machine and the Raspberry Pi library will be mocked out (permitting you to ensure the right values are coming through).

I know, it's not great.

## Limitations

The handbrake feature doesn't work- I haven't found a good way to statelessly lock the rear wheels.

If you're accelerating forwards, transitioning to full braking locks the wheels, but if you're reversing, transitioning to full throttle spins the wheels the other way.

I've tried killing the PWM altogether in the hope it'll lock wheels but it doesn't seem to work.   
