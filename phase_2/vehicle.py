import socket
import sys
import time
from threading import Event, Thread

if sys.platform != 'linux2':
    from mock import MagicMock

    pigpio = MagicMock()
else:
    import pigpio

pi = pigpio.pi()

FREQ = 50.0
MIN_DUTY = 5
IDLE_DUTY = 7.5
MAX_DUTY = 10.0

STEERING = 12
THROTTLE = 19

pi.set_PWM_frequency(STEERING, FREQ)
pi.set_PWM_dutycycle(STEERING, IDLE_DUTY)

pi.set_PWM_frequency(THROTTLE, FREQ)
pi.set_PWM_dutycycle(THROTTLE, IDLE_DUTY)


def combine_brake_and_accelerator(brake, accelerator):
    brake += 1.0
    brake = -brake
    accelerator += 1.0

    return (brake + accelerator) / 2.0


def rescale(value):
    return 10.0 - (((value - -1.0) * (MAX_DUTY - MIN_DUTY)) / (1.0 - -1.0))


def rescale_for_255(value):
    return (value / 100.0) * 255.0


class PS4Receiver(Thread):
    def __init__(self, throttle, steering):
        super(PS4Receiver, self).__init__()

        self.throttle = throttle
        self.steering = steering

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 6291))
        self.socket.settimeout(0.2)

        self.stop_event = Event()

    def stop(self):
        self.stop_event.set()

        pi.set_PWM_frequency(self.steering, 0)
        pi.set_PWM_dutycycle(self.steering, 0)

        pi.set_PWM_dutycycle(self.throttle, 0)
        pi.set_PWM_frequency(self.throttle, 0)

    def run(self):
        last_state = None

        while not self.stop_event.is_set():
            try:
                data, addr = self.socket.recvfrom(65536)
                steering, brake, accelerator, handbrake = eval(data)
            except socket.timeout:
                steering, brake, accelerator, handbrake = last_state[0], -1.0, -1.0, True

            state = [steering, brake, accelerator, handbrake]
            if state == last_state:
                continue

            last_state = state

            # invert the steering
            if steering < 0:
                steering = 2 - (steering + 2)
            elif steering > 0:
                steering = -2 - (steering - 2)

            steering_duty_cycle = rescale(steering)
            brake_and_accelerator = combine_brake_and_accelerator(brake, accelerator)
            throttle_duty_cycle = rescale(brake_and_accelerator)

            print '\t'.join([
                str(x) for x in [steering_duty_cycle, throttle_duty_cycle, handbrake]
            ])

            pi.set_PWM_dutycycle(self.steering, rescale_for_255(steering_duty_cycle))
            pi.set_PWM_dutycycle(self.throttle, rescale_for_255(throttle_duty_cycle))


r = PS4Receiver(STEERING, THROTTLE)
r.start()

while 1:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        break

r.stop()
r.join()
