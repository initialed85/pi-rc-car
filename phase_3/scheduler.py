import datetime
import time

from threading import Thread, Event, RLock


class Scheduler(Thread):
    def __init__(self, period):
        super(Scheduler, self).__init__()

        self.period = period

        self.stop_event = Event()
        self.iteration_callback = None
        self.state = None

        self.lock = RLock()

    def stop(self):
        self.stop_event.set()

    def set_iteration_callback(self, iteration_callback):
        if not callable(iteration_callback):
            raise TypeError('expected {} to be callable but it was not'.format(repr(iteration_callback)))

        self.iteration_callback = iteration_callback

    def set_state(self, state):
        with self.lock:
            self.state = state

    def run(self):
        timedelta = datetime.timedelta(seconds=self.period)

        while not self.stop_event.is_set():
            started = datetime.datetime.now()
            planned_stop = started + timedelta

            if self.iteration_callback is not None:
                with self.lock:
                    self.iteration_callback(self.state)

            stopped = datetime.datetime.now()

            if stopped < planned_stop:
                time.sleep((planned_stop - stopped).total_seconds())
