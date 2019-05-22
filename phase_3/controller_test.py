import unittest

from mock import patch, call, Mock
from pygame import JOYAXISMOTION, JOYBUTTONDOWN, JOYBUTTONUP, JOYHATMOTION
from pygame.event import Event

from controller import Controller


def some_method():
    pass


_TEST_INITIAL_AXIS_DATA = {}

_TEST_INITIAL_BUTTON_DATA = {
    0: False,
    1: False
}

_TEST_INITIAL_HAT_DATA = {
    0: (0, 0),
    1: (0, 0)
}

_TEST_EVENT_1 = Mock(spec=Event)
_TEST_EVENT_1.type = JOYAXISMOTION
_TEST_EVENT_1.axis = 0
_TEST_EVENT_1.value = -0.03

_TEST_EVENT_2 = Mock(spec=Event)
_TEST_EVENT_2.type = JOYAXISMOTION
_TEST_EVENT_2.axis = 4
_TEST_EVENT_2.value = -1.0

_TEST_EVENT_3 = Mock(spec=Event)
_TEST_EVENT_3.type = JOYAXISMOTION
_TEST_EVENT_3.axis = 5
_TEST_EVENT_3.value = -1.0

_TEST_EVENT_4 = Mock(spec=Event)
_TEST_EVENT_4.type = JOYBUTTONDOWN
_TEST_EVENT_4.button = 0

_TEST_EVENT_5 = Mock(spec=Event)
_TEST_EVENT_5.button = 1
_TEST_EVENT_5.type = JOYBUTTONUP

_TEST_EVENT_6 = Mock(spec=Event)
_TEST_EVENT_6.type = JOYHATMOTION
_TEST_EVENT_6.hat = 0
_TEST_EVENT_6.value = (1, 1)

_TEST_EVENTS = [_TEST_EVENT_1, _TEST_EVENT_2, _TEST_EVENT_3, _TEST_EVENT_4, _TEST_EVENT_5, _TEST_EVENT_6]

_TEST_AXIS_DATA = {
    0: -0.03,
    4: -1.0,
    5: -1.0,
}

_TEST_BUTTON_DATA = {
    0: True,
    1: False,
}

_TEST_HAT_DATA = {
    0: (1, 1),
    1: (0, 0),
}

_TEST_STATE = {
    'brake': -1.0,
    'steering': 0.0,
    'accelerator': -1.0,
    'handbrake': False
}


class ControllerTest(unittest.TestCase):
    @patch('controller.pygame')
    def setUp(self, pygame):
        self.pygame = pygame

        self.subject = Controller()

        self.subject.controller.get_numbuttons.return_value = 2
        self.subject.controller.get_numhats.return_value = 2

    def test_init(self):
        self.assert_(
            self.pygame.mock_calls == [
                call.init(),
                call.joystick.init(),
                call.joystick.Joystick(0),
                call.joystick.Joystick().init()
            ]
        )

    def test_set_state_change_callback(self):
        self.subject.set_state_change_callback(some_method)

        self.assert_(self.subject.state_change_callback == some_method)

    def test_get_initial_datas(self):
        axis_data, button_data, hat_data = self.subject.get_initial_datas()

        self.assert_(axis_data == _TEST_INITIAL_AXIS_DATA)

        self.assert_(button_data == _TEST_INITIAL_BUTTON_DATA)

        self.assert_(hat_data == _TEST_INITIAL_HAT_DATA)

    def test_handle_event(self):
        self.subject.controller.get_numbuttons.return_value = 2
        self.subject.controller.get_numhats.return_value = 2

        axis_data, button_data, hat_data = self.subject.get_initial_datas()

        for event in _TEST_EVENTS:
            axis_data, button_data, hat_data = self.subject.handle_event(
                event, axis_data, button_data, hat_data
            )

        self.assert_(axis_data == _TEST_AXIS_DATA)

        self.assert_(button_data == _TEST_BUTTON_DATA)

        self.assert_(hat_data == _TEST_HAT_DATA)

    def test_get_state(self):
        state = self.subject.build_state(_TEST_AXIS_DATA, _TEST_BUTTON_DATA, _TEST_HAT_DATA)

        self.assert_(state == _TEST_STATE)

    @patch('controller.pygame.event')
    def test_iterate(self, event):
        self.subject.state_change_callback = Mock()

        event.get.return_value = _TEST_EVENTS

        axis_data, button_data, hat_data = self.subject.get_initial_datas()

        axis_data, button_data, hat_data, last_state = self.subject.iterate(axis_data, button_data, hat_data, None)

        self.assert_(self.subject.state_change_callback.mock_calls == [
            call({'brake': None, 'steering': 0.0, 'accelerator': None, 'handbrake': False}),
            call({'brake': -1.0, 'steering': 0.0, 'accelerator': None, 'handbrake': False}),
            call({'brake': -1.0, 'steering': 0.0, 'accelerator': -1.0, 'handbrake': False})
        ])

        self.assert_(axis_data == _TEST_AXIS_DATA)
        self.assert_(button_data == _TEST_BUTTON_DATA)
        self.assert_(hat_data == _TEST_HAT_DATA)

    def test_loop(self):
        self.subject.get_initial_datas = Mock()
        self.subject.get_initial_datas.return_value = 1, 2, 3

        self.subject.iterate = Mock()
        self.subject.iterate.return_value = 1, 2, 3, 4

        self.subject.loop(test_mode=True)

        self.assert_(self.subject.get_initial_datas.mock_calls == [
            call()
        ])

        self.assert_(self.subject.iterate.mock_calls == [
            call(1, 2, 3, None)
        ])
