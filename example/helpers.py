import sys
import time


def console(msg):
    """Print something to stderr immediately (flush it).
    """
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


class Timestamp:
    """Record elapsed time from a specific moment.
    """
    def __init__(self):
        """Upon creation, an instance records the current time.
        """
        self.stamp = time.time()

    def elapsed(self):
        """Produce the time that has elapsed since the instance was created.

        The representation is in seconds, with 2 decimals if the number of seconds
        is less than 10, else without decimals.
        """
        interval = time.time() - self.stamp
        if interval < 10:
            return f"{interval:5.2f}s"
        interval = int(round(interval))
        return f"{interval:>2d}s   "
