import datetime
import socket
import time
from threading import Thread, Event, RLock

import pygame


class Transmitter(Thread):
    def __init__(self, ip, port, period):
        super(Transmitter, self).__init__()

        self.ip = ip
        self.port = port
        self.period = period

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.stop_event = Event()
        self.state = None
        self.lock = RLock()

    def get_state(self):
        with self.lock:
            return self.state

    def set_state(self, state):
        with self.lock:
            self.state = state

    def stop(self):
        self.stop_event.set()

    def run(self):
        delta = datetime.timedelta(seconds=self.period)

        while not self.stop_event.is_set():
            started = datetime.datetime.now()
            planned_stop = started + delta

            state = self.get_state()
            if state is not None and None not in state:

                try:
                    self.socket.sendto(repr(self.state), (self.ip, self.port))
                except socket.error:
                    pass

            stopped = datetime.datetime.now()
            if stopped < planned_stop:
                time.sleep((planned_stop - stopped).total_seconds())


class Controller(object):
    def __init__(self, transmitter, period):
        self.transmitter = transmitter
        self.period = period

        pygame.init()
        pygame.joystick.init()

        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()

    def listen(self):
        axis_data = {}

        button_data = {}
        for i in range(self.controller.get_numbuttons()):
            button_data[i] = False

        hat_data = {}
        for i in range(self.controller.get_numhats()):
            hat_data[i] = (0, 0)

        last_state = None

        while 1:
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    axis_data[event.axis] = round(event.value, 2)
                elif event.type == pygame.JOYBUTTONDOWN:
                    button_data[event.button] = True
                elif event.type == pygame.JOYBUTTONUP:
                    button_data[event.button] = False
                elif event.type == pygame.JOYHATMOTION:
                    hat_data[event.hat] = event.value

                if None in [axis_data, button_data]:
                    time.sleep(self.period)
                    continue

                steering = axis_data.get(0)
                brake = axis_data.get(4)
                accelerator = axis_data.get(5)
                handbrake = button_data.get(1)

                if None in [steering, brake, accelerator, handbrake]:
                    time.sleep(self.period)
                    continue

                # steering deadzone
                if -0.04 <= steering <= 0.04:
                    steering = 0.0

                state = [steering, brake, accelerator, handbrake]

                if state == last_state:
                    time.sleep(self.period)
                    continue

                print '\t'.join([str(x) for x in state])

                last_state = state

                self.transmitter.set_state(state)


if __name__ == '__main__':
    import sys

    t = Transmitter(
        ip=sys.argv[1],
        port=6291,
        period=(1.0 / 50) / 2,
    )

    c = Controller(
        transmitter=t,
        period=(1.0 / 50) / 2,
    )

    t.start()
    try:
        c.listen()
    except KeyboardInterrupt:
        pass

    t.stop()
    t.join()
