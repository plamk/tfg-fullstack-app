import signal
import atexit
import threading
import gpiod


class Light:
    def __init__(self, chip_name="gpiochip0", line_num=17):
        self._lock = threading.Lock()
        self._chip = gpiod.Chip(chip_name)
        self._line = self._chip.get_line(line_num)
        # request once and keep it for process lifetime
        self._line.request(consumer="myapp", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
        self._closed = False

    def turn_on(self):
        with self._lock:
            if self._closed:
                return
            self._line.set_value(1)

    def turn_off(self):
        with self._lock:
            if self._closed:
                return
            self._line.set_value(0)

    def close(self):
        with self._lock:
            if self._closed:
                return
            try:
                self._line.set_value(0)
            except Exception:
                pass
            try:
                self._line.release()
            except Exception:
                pass
            try:
                self._chip.close()
            except Exception:
                pass
            self._closed = True

    @property
    def is_closed(self):
        with self._lock:
            return self._closed
