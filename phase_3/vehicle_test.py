import copy
import unittest

from mock import patch, call, Mock

from vehicle import convert_ps4_value_to_duty_cycle_percent, combine_brake_and_accelerator, \
    convert_duty_cycle_percent_to_8_bit, Vehicle, STEERING_GPIO, THROTTLE_GPIO, FREQUENCY, MIN_DUTY, IDLE_DUTY, \
    MAX_DUTY, TIMEOUT


class HelperFunctionTest(unittest.TestCase):
    def test_convert_ps4_value_to_duty_cycle_percent(self):
        self.assert_(convert_ps4_value_to_duty_cycle_percent(-1.0) == 10.0)
        self.assert_(convert_ps4_value_to_duty_cycle_percent(0.0) == 7.5)
        self.assert_(convert_ps4_value_to_duty_cycle_percent(1.0) == 5.0)

    def test_combine_brake_and_accelerator(self):
        self.assert_(combine_brake_and_accelerator(0.75, 0.25) == -0.25)

    def test_convert_duty_cycle_percent_to_8_bit(self):
        self.assert_(convert_duty_cycle_percent_to_8_bit(50) == 127.5)


_TEST_STATE = {
    'brake': 0.0,
    'steering': 0.13,
    'accelerator': 1.0,
    'handbrake': False
}

_TEST_SAFE_STATE = {
    'brake': -1.0,
    'steering': 0.13,
    'accelerator': -1.0,
    'handbrake': True,
}


class VehicleTest(unittest.TestCase):
    @patch('vehicle.pigpio')
    def setUp(self, pigpio):
        self.subject = Vehicle(
            STEERING_GPIO,
            THROTTLE_GPIO,
            FREQUENCY,
            MIN_DUTY,
            IDLE_DUTY,
            MAX_DUTY,
            TIMEOUT,
        )

        self.assert_(pigpio.mock_calls == [
            call.pi(),
            call.pi().set_PWM_frequency(12, 50.0),
            call.pi().set_PWM_dutycycle(12, convert_duty_cycle_percent_to_8_bit(7.5)),
            call.pi().set_PWM_frequency(19, 50.0),
            call.pi().set_PWM_dutycycle(19, convert_duty_cycle_percent_to_8_bit(7.5)),
        ])

        self.subject.pi.mock_calls = []

    def test_set_pwm(self):
        self.subject.set_pwm(STEERING_GPIO, 49, 7.6)
        self.subject.set_pwm(STEERING_GPIO, 49, 7.6)

        # note- two calls to set_pwm, only one call to the library
        self.assert_(
            self.subject.pi.mock_calls == [
                call.set_PWM_frequency(12, 49),
                call.set_PWM_dutycycle(12, 19.38)
            ]
        )

    def test_handle_queue(self):
        self.subject.state_queue.put(_TEST_STATE)

        last_state = copy.deepcopy(_TEST_STATE)

        state = self.subject.handle_queue(last_state)
        self.assert_(state == _TEST_STATE)

        state = self.subject.handle_queue(state)
        self.assert_(state == _TEST_SAFE_STATE)

    def test_iterate(self):
        self.subject.handle_queue = Mock()
        self.subject.handle_queue.return_value = _TEST_STATE
        self.subject.set_pwm = Mock()

        last_state = copy.deepcopy(_TEST_STATE)
        last_state['handbrake'] = True

        state = self.subject.iterate(last_state)

        self.assert_(state == _TEST_STATE)

        self.assert_(self.subject.set_pwm.mock_calls == [
            call(12, 50.0, 7.824999999999999),
            call(19, 50.0, 6.25)
        ])

    def test_stop(self):
        self.subject.stop_event = Mock()
        self.subject.stop()

        self.assert_(self.subject.stop_event.mock_calls == [
            call.set()
        ])

    def test_run(self):
        self.subject.iterate = Mock()

        self.subject.run(test_mode=True)

        self.assert_(self.subject.iterate.mock_calls == [call(None)])
