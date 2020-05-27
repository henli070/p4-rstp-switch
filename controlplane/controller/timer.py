from threading import Thread, Condition
import datetime

class Timer(Thread):
    """Startable and stoppable repeating timer, which runs in its own thread."""
    STATE_STOPPED = 0
    STATE_RESTART = 1
    STATE_RUNNING = 2
    STATE_CANCELED = 3

    def __init__(self, callback):
        Thread.__init__(self)
        self.daemon = True

        self.callback = callback
        self.state = Timer.STATE_STOPPED
        self.condition = Condition()

        Thread.start(self)

    def run(self):
        while True:
            # Wait until started.
            self.condition.acquire()
            while self.state == Timer.STATE_STOPPED:
                self.condition.wait()
                if self.state == Timer.STATE_CANCELED:
                    self.condition.release()
                    return

            if self.state == Timer.STATE_RESTART:
                self.call_time = datetime.datetime.now()
                self.state = Timer.STATE_RUNNING

            # Wait the delay.
            self.call_time += datetime.timedelta(seconds=self.delay)
            self.condition.wait((self.call_time - datetime.datetime.now()).total_seconds())

            if self.state == Timer.STATE_CANCELED:
                self.condition.release()
                return
            if self.state != Timer.STATE_RUNNING:
                self.condition.release()
                continue
            self.condition.release()

            self.callback()

    def is_active(self):
        return self.state == Timer.STATE_RUNNING or self.state == Timer.STATE_RESTART

    def start(self, delay):
        self.condition.acquire()
        self.delay = delay
        self.state = Timer.STATE_RESTART
        self.condition.notify()
        self.condition.release()

    def stop(self):
        self.condition.acquire()
        self.state = Timer.STATE_STOPPED
        self.condition.notify()
        self.condition.release()

    def cancel(self):
        self.condition.acquire()
        self.state = Timer.STATE_CANCELED
        self.condition.notify()
        self.condition.release()
        self.join()

