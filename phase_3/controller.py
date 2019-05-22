import time
import traceback

import pygame

DEBOUNCE_PERIOD = 1.0 / 50.0


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
    def build_state(axis_data, button_data, hat_data):
        steering = axis_data.get(0)
        brake = axis_data.get(4)
        accelerator = axis_data.get(5)
        stop = button_data.get(0)
        turbo = button_data.get(1)
        record = button_data.get(2)
        play = button_data.get(3)

        # create steering deadzone
        if steering is not None and -0.04 <= steering <= 0.04:
            steering = 0.0

        if brake is not None and not turbo:
            brake_range = 0.5883
            brake = (brake * (brake_range / 2)) - (1 - (brake_range / 2))

        if accelerator is not None and not turbo:
            accelerator_range = 0.0393
            accelerator = (accelerator * (accelerator_range / 2)) - (1 - (accelerator_range / 2))

        state = {
            'steering': steering,
            'brake': brake,
            'accelerator': accelerator,
            'stop': stop,
            'record': record,
            'play': play,
        }

        return state

    def iterate(self, axis_data, button_data, hat_data, last_state):
        for event in pygame.event.get():
            axis_data, button_data, hat_data = self.handle_event(event, axis_data, button_data, hat_data)
            if None in [axis_data, button_data, hat_data]:
                time.sleep(DEBOUNCE_PERIOD)
                continue

            state = self.build_state(axis_data, button_data, hat_data)
            if None in state:
                time.sleep(DEBOUNCE_PERIOD)
                continue

            if state == last_state:
                time.sleep(DEBOUNCE_PERIOD)
                continue

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
    from publisher import Publisher
    from scheduler import Scheduler

    import sys

    p = Publisher(
        host=sys.argv[1],
        port=13337,
    )

    s = Scheduler(period=DEBOUNCE_PERIOD)
    s.start()
    s.set_iteration_callback(p.send)

    c = Controller()
    c.set_state_change_callback(s.set_state)

    try:
        c.loop()
    except KeyboardInterrupt:
        pass

    s.stop()
    s.join()
