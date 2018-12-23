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

FREQ = 50.0

MIN_DUTY = 5.0
IDLE_DUTY = 7.5
MAX_DUTY = 10.0

s = GPIO.PWM(35, FREQ)
s.start(IDLE_DUTY)

t = GPIO.PWM(32, FREQ)
t.start(IDLE_DUTY)


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
        while not self.stop_event.is_set():
            try:
                data, addr = self.socket.recvfrom(65536)
            except socket.timeout:
                self.throttle.start(IDLE_DUTY)
                continue

            if data == 'KEEPALIVE':
                time.sleep(0.01)
                continue

            steering, brake, accelerator = eval(data)

            # invert the steering
            if steering < 0:
                steering = 2 - (steering + 2)
            elif steering > 0:
                steering = -2 - (steering - 2)

            steering_duty_cycle = rescale(steering)
            brake_and_accelerator = combine_brake_and_accelerator(brake, accelerator)
            throttle_duty_cycle = rescale(brake_and_accelerator)

            print '\t'.join([str(x) for x in [steering_duty_cycle, throttle_duty_cycle]])

            self.steering.start(steering_duty_cycle)
            self.throttle.start(throttle_duty_cycle)


r = PS4Receiver(t, s)
r.start()

while 1:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        break

r.stop()
r.join()
