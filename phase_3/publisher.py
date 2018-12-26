import socket


class Publisher(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, state):
        try:
            self.socket.sendto(repr(state), (self.host, self.port))
        except socket.error:
            pass
