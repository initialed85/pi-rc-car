import socket
import time
from threading import Event, Thread

try:
    from RPi import GPIO
except Exception:
    from mock import MagicMock

    GPIO = MagicMock()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(35, GPIO.OUT)
GPIO.setup(32, GPIO.OUT)

FREQ = 51.0
MIN_DUTY = 5
IDLE_DUTY = 7.5
MAX_DUTY = 10.0

STEERING = 35
THROTTLE = 32

steering = GPIO.PWM(STEERING, FREQ)
steering.start(IDLE_DUTY)

throttle = GPIO.PWM(THROTTLE, FREQ)
throttle.start(IDLE_DUTY)


def combine_brake_and_accelerator(brake, accelerator):
    brake += 1.0
    brake = -brake
    accelerator += 1.0

    return (brake + accelerator) / 2.0


def rescale(value):
    return 10.0 - (((value - -1.0) * (MAX_DUTY - MIN_DUTY)) / (1.0 - -1.0))


class PS4Receiver(Thread):
    def __init__(self, throttle, steering):
        super(PS4Receiver, self).__init__()

        self.throttle = throttle
        self.steering = steering

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 6291))
        self.socket.settimeout(0.2)  # twice the keepalive period

        self.stop_event = Event()

    def stop(self):
        self.stop_event.set()

    def run(self):
        last_state = None

        while not self.stop_event.is_set():
            try:
                data, addr = self.socket.recvfrom(65536)
            except socket.timeout:
                self.throttle.start(IDLE_DUTY)
                continue

            if data == 'KEEPALIVE':
                continue

            steering, brake, accelerator = eval(data)

            state = [steering, brake, accelerator]
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

            print [steering_duty_cycle, throttle_duty_cycle]

            self.steering.ChangeDutyCycle(steering_duty_cycle)
            self.throttle.ChangeDutyCycle(throttle_duty_cycle)


r = PS4Receiver(steering, throttle)
r.start()

while 1:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        break

r.stop()
r.join()
