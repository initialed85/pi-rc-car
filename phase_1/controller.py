import socket
import time

import pygame


class PS4Transmitter(object):
    def __init__(self, ip, *args, **kwargs):
        super(PS4Transmitter, self).__init__(*args, **kwargs)

        self.ip = ip

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.controller = None
        self.axis_data = None
        self.button_data = None
        self.hat_data = None
        self.state = None

        pygame.init()
        pygame.joystick.init()

        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()

    def send_keepalive_and_sleep(self):
        self.socket.sendto('KEEPALIVE', (self.ip, 6291))
        time.sleep(0.01)

    def listen(self):
        if not self.axis_data:
            self.axis_data = {}

        if not self.button_data:
            self.button_data = {}
            for i in range(self.controller.get_numbuttons()):
                self.button_data[i] = False

        if not self.hat_data:
            self.hat_data = {}
            for i in range(self.controller.get_numhats()):
                self.hat_data[i] = (0, 0)

        while 1:
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    self.axis_data[event.axis] = round(event.value, 2)
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.button_data[event.button] = True
                elif event.type == pygame.JOYBUTTONUP:
                    self.button_data[event.button] = False
                elif event.type == pygame.JOYHATMOTION:
                    self.hat_data[event.hat] = event.value

                if self.axis_data is None:
                    self.send_keepalive_and_sleep()
                    continue

                steering = self.axis_data.get(0)
                brake = self.axis_data.get(4)
                accelerator = self.axis_data.get(5)

                if None in [steering, brake, accelerator]:
                    self.send_keepalive_and_sleep()
                    continue

                # steering deadzone
                if -0.04 <= steering <= 0.04:
                    steering = 0.0

                state = [steering, brake, accelerator]

                if state == self.state:
                    self.send_keepalive_and_sleep()
                    continue

                try:
                    self.socket.sendto(repr(state), (self.ip, 6291))
                except socket.error:
                    self.send_keepalive_and_sleep()

                self.state = state


if __name__ == '__main__':
    from sys import argv

    ps4 = PS4Transmitter(argv[1])

    ps4.listen()
