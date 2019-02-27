import socket
import time


class Tello(object):
    def __init__(self, host='192.168.10.1', port=8889, listen_port=9000):
        self.host = host
        self.port = port
        self.listen_port = listen_port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 9000))

        self.socket.sendto('command', (self.host, self.port))
        time.sleep(1)
        self.socket.sendto('streamon', (self.host, self.port))
        time.sleep(1)
        self.socket.sendto('takeoff', (self.host, self.port))

    def send(self, state):
        print state
        if state is None:
            return

        combined_throttle = state.get('combined_throttle')
        pitch = state.get('pitch')
        roll = state.get('roll')
        yaw = state.get('yaw')

        if None in [combined_throttle, pitch, roll, yaw]:
            return

        try:
            self.socket.sendto(
                'rc {} {} {} {}'.format(
                    roll,
                    pitch,
                    combined_throttle,
                    yaw,
                ),
                (self.host, self.port)
            )
        except socket.error:
            pass
