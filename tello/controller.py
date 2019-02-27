import time
import traceback

import pygame

from tello import Tello

DEBOUNCE_PERIOD = 1.0 / 20.0


class Controller(object):
    def __init__(self, state_change_callback=None):
        pygame.init()
        pygame.joystick.init()

        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()

        self.state_change_callback = None

        if state_change_callback is not None:
            self.set_state_change_callback(state_change_callback)

    def set_state_change_callback(self, state_change_callback):
        if not callable(state_change_callback):
            raise TypeError('expected {} to be callable but it was not'.format(repr(state_change_callback)))

        self.state_change_callback = state_change_callback

    def get_initial_datas(self):
        axis_data = {}

        button_data = {}
        for i in range(self.controller.get_numbuttons()):
            button_data[i] = False

        hat_data = {}
        for i in range(self.controller.get_numhats()):
            hat_data[i] = (0, 0)

        return axis_data, button_data, hat_data

    @staticmethod
    def handle_event(event, axis_data, button_data, hat_data):
        if event.type == pygame.JOYAXISMOTION:
            axis_data[event.axis] = round(event.value, 2)
        elif event.type == pygame.JOYBUTTONDOWN:
            button_data[event.button] = True
        elif event.type == pygame.JOYBUTTONUP:
            button_data[event.button] = False
        elif event.type == pygame.JOYHATMOTION:
            hat_data[event.hat] = event.value

        return axis_data, button_data, hat_data

    @staticmethod
    def get_state(axis_data, button_data, hat_data):
        if axis_data is not None:
            for i in range(0, 4):
                axis_value = axis_data.get(i)
                if axis_value is None:
                    continue

                # handle stick deadzones
                if -0.04 <= axis_value <= 0.04:
                    axis_data[i] = 0

        throttle = axis_data.get(5)
        if throttle is not None:
            throttle = ((throttle - 1) / 2) * 100

        brake = axis_data.get(4)
        if brake is not None:
            brake = ((brake + 1) / 2) * 100

        combined_throttle = None
        if throttle is not None and brake is not None:
            combined_throttle = -int(-100 - throttle + brake)

        pitch = axis_data.get(1)
        if pitch is not None:
            pitch = int(pitch * -100)

        roll = axis_data.get(2)
        if roll is not None:
            roll = int(roll * 100)

        yaw = axis_data.get(0)
        if yaw is not None:
            yaw = int(yaw * 100)

        return {
            'combined_throttle': combined_throttle,
            'pitch': pitch,
            'roll': roll,
            'yaw': yaw,
        }

    def iterate(self, axis_data, button_data, hat_data, last_state):
        for event in pygame.event.get():
            axis_data, button_data, hat_data = self.handle_event(event, axis_data, button_data, hat_data)
            if None in [axis_data, button_data, hat_data]:
                time.sleep(DEBOUNCE_PERIOD)
                continue

            state = self.get_state(axis_data, button_data, hat_data)
            if None in state:
                time.sleep(DEBOUNCE_PERIOD)
                continue

            if state == last_state:
                time.sleep(DEBOUNCE_PERIOD)
                continue

            # print '\t'.join([str(x) for x in state.values()])

            if self.state_change_callback is not None:
                try:
                    self.state_change_callback(state)
                except Exception:
                    traceback.print_exc()

            last_state = state

        return axis_data, button_data, hat_data, last_state

    def loop(self, test_mode=False):
        axis_data, button_data, hat_data = self.get_initial_datas()

        last_state = None

        while 1:
            axis_data, button_data, hat_data, last_state = self.iterate(
                axis_data, button_data, hat_data, last_state
            )

            if test_mode:
                break


if __name__ == '__main__':
    from scheduler import Scheduler

    t = Tello()

    s = Scheduler(period=DEBOUNCE_PERIOD)
    s.start()
    s.set_iteration_callback(t.send)

    c = Controller()
    c.set_state_change_callback(s.set_state)

    try:
        c.loop()
    except KeyboardInterrupt:
        pass

    s.stop()
    s.join()
