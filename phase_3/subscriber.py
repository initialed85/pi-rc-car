import socket
import traceback
from threading import Thread, Event


class Subscriber(Thread):
    def __init__(self, port, timeout):
        super(Subscriber, self).__init__()

        self.port = port
        self.timeout = timeout

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.port))
        self.socket.settimeout(self.timeout)

        self.stop_event = Event()

        self.receive_callback = None

    def set_receive_callback(self, receive_callback):
        if not callable(receive_callback):
            raise TypeError('expected {} to be callable but it was not'.format(repr(receive_callback)))

        self.receive_callback = receive_callback

    def stop(self):
        self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            try:
                data, addr = self.socket.recvfrom(65536)
                state = eval(data)
                self.receive_callback(state)
            except socket.timeout:
                pass
            except Exception:
                traceback.print_exc()
