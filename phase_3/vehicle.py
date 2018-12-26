import sys
from Queue import Queue, Empty
from threading import Thread, Event

if sys.platform != 'linux2':
    from mock import MagicMock

    pigpio = MagicMock()
else:
    import pigpio

STEERING_GPIO = 19
THROTTLE_GPIO = 12

FREQUENCY = 50.0
MIN_DUTY = 5.0
IDLE_DUTY = 7.5
MAX_DUTY = 10.0

TIMEOUT = (1.0 / FREQUENCY) * 2


def convert_ps4_value_to_duty_cycle_percent(value):
    return 10.0 - (((value - -1.0) * (MAX_DUTY - MIN_DUTY)) / (1.0 - -1.0))


def combine_brake_and_accelerator(brake, accelerator):
    brake += 1.0
    brake = -brake
    accelerator += 1.0

    return (brake + accelerator) / 2.0


def convert_duty_cycle_percent_to_8_bit(value):
    return (value / 100.0) * 255.0


class Vehicle(Thread):
    def __init__(self, steering_gpio, throttle_gpio, frequency, min_duty, idle_duty, max_duty, timeout):
        super(Vehicle, self).__init__()

        self.steering_gpio = steering_gpio
        self.throttle_gpio = throttle_gpio
        self.frequency = frequency
        self.min_duty = min_duty
        self.idle_duty = idle_duty
        self.max_duty = max_duty
        self.timeout = timeout

        self.pi = pigpio.pi()

        self.last_frequency_by_gpio = {}
        self.last_duty_by_gpio = {}

        self.set_pwm(self.steering_gpio, self.frequency, self.idle_duty)
        self.set_pwm(self.throttle_gpio, self.frequency, self.idle_duty)

        self.stop_event = Event()

        self.state_queue = Queue()

    def set_pwm(self, gpio, frequency, duty):
        duty = convert_duty_cycle_percent_to_8_bit(duty)

        last_frequency = self.last_frequency_by_gpio.get(gpio)
        if last_frequency is None or last_frequency != frequency:
            self.pi.set_PWM_frequency(gpio, frequency)
            self.last_frequency_by_gpio[gpio] = frequency

        last_duty = self.last_duty_by_gpio.get(gpio)
        if last_duty is None or last_duty != duty:
            self.pi.set_PWM_dutycycle(gpio, duty)
            self.last_duty_by_gpio[gpio] = duty

    def handle_queue(self, last_state):
        try:
            return self.state_queue.get(timeout=self.timeout)
        except Empty:
            return {
                'brake': -1.0,
                'steering': last_state.get('steering') if last_state is not None else 0.0,
                'accelerator': -1.0,
                'handbrake': True,
            }

    def iterate(self, last_state):
        state = self.handle_queue(last_state)
        if state is None or None in state.values() or state == last_state:
            return last_state

        # invert the steering
        steering = state['steering']
        if steering < 0:
            steering = 2 - (steering + 2)
        elif steering > 0:
            steering = -2 - (steering - 2)

        steering_duty_cycle = convert_ps4_value_to_duty_cycle_percent(steering)

        throttle_duty_cycle = convert_ps4_value_to_duty_cycle_percent(
            combine_brake_and_accelerator(
                state['brake'],
                state['accelerator'],
            )
        )

        handbrake = state['handbrake']

        print '\t'.join([
            str(x) for x in [steering_duty_cycle, throttle_duty_cycle, handbrake]
        ])

        self.set_pwm(self.steering_gpio, self.frequency, steering_duty_cycle)
        self.set_pwm(self.throttle_gpio, self.frequency, throttle_duty_cycle)

        return state

    def add_state_event(self, state):
        self.state_queue.put(state)

    def stop(self):
        self.stop_event.set()

    def run(self, test_mode=False):
        last_state = None
        while not self.stop_event.is_set():
            last_state = self.iterate(last_state)
            if test_mode:
                break


if __name__ == '__main__':
    import time
    from subscriber import Subscriber

    v = Vehicle(
        STEERING_GPIO,
        THROTTLE_GPIO,
        FREQUENCY,
        MIN_DUTY,
        IDLE_DUTY,
        MAX_DUTY,
        TIMEOUT,
    )
    v.start()

    s = Subscriber(
        port=6291,
        timeout=TIMEOUT * 2,
    )
    s.start()

    s.set_receive_callback(v.add_state_event)

    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    s.stop()
    s.join()

    v.stop()
    v.join()
