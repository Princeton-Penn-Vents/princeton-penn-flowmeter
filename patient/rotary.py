#!/usr/bin/env python3

import sys
import time
import threading

try:
    import pigpio
except ImportError:
    # in case we're loading this just for the MockRotary
    pass


class Setting:
    def __init__(self, *, unit):
        self.unit = unit
        self._lock = threading.Lock()

    def __str__(self):
        unit = "" if self.unit is None else f" {self.unit}"
        return f"{self.value}{unit}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self})"

    def __format__(self, format_spec):
        return str(self).__format__(format_spec)


class IncrSetting(Setting):
    def __init__(self, default, *, min, max, incr, unit=None):
        "Note: incr should be a nice floating point number"

        super().__init__(unit=unit)

        self._min = min
        self._max = max
        self._value = default
        self._incr = incr

    def up(self):
        with self._lock:
            if self._value < self._max:
                self._value += self._incr
                return True
            else:
                return False

    def down(self):
        with self._lock:
            if self._value > self._min:
                self._value -= self._incr
                return True
            else:
                return False

    @property
    def value(self):
        with self._lock:
            return self._value


class SelectionSetting(Setting):
    def __init__(self, default, listing, *, unit=None):

        super().__init__(unit=unit)

        assert 0 < default < len(listing)

        self._value = default
        self._listing = listing

    def up(self):
        with self._lock:
            if self._value < len(self._listing) - 1:
                self._value += 1
                return True
            else:
                return False

    def down(self):
        with self._lock:
            if self._value > 0:
                self._value -= 1
                return True
            else:
                return False

    @property
    def value(self):
        with self._lock:
            return self._listing[self._value]


DICT = {
    "PIP Max": IncrSetting(30, min=0, max=40, incr=1, unit="cm-H2O"),
    "PIP Min": IncrSetting(5, min=0, max=20, incr=1, unit="cm-H2O"),
    "PEEP Max": IncrSetting(8, min=0, max=15, incr=1, unit="cm-H2O"),
    "PEEP Min": IncrSetting(0, min=0, max=15, incr=1, unit="cm-H2O"),
    "TVe Max": IncrSetting(700, min=100, max=1000, incr=50, unit="ml"),
    "TVe Min": IncrSetting(300, min=100, max=1000, incr=50, unit="ml"),
    "TVi Max": IncrSetting(700, min=100, max=1000, incr=50, unit="ml"),
    "TVi Min": IncrSetting(300, min=100, max=1000, incr=50, unit="ml"),
    "AvgWindow": SelectionSetting(2, [10, 15, 30, 60], unit="sec"),
    "Alarm Reset": SelectionSetting(2, [10, 15, 30, 60], unit="sec"),
    "Sensor ID": IncrSetting(1, min=1, max=20, incr=1),  # REQUIRED
}


class MockRotary:

    def __init__(self, d):
        self.dict = d

    def __getitem__(self, item):
        return self.dict[item]

    def close(self):
        pass

    def __del__(self):
        pass

    def __repr__(self):
        out = f"{self.__class__.__name__}(\n"
        for key, value in self.dict.items():
            out += f"  {key} : {value}\n"
        return out + "\n)"


class Rotary:
    def turned_display(self, up):
        "Override in subclass to customize"
        dir = "up" if up else "down"
        print(f"Changed {self.items[self.current]} {dir}")
        print(rotary)

    def pushed_display(self):
        "Override in subclass to customize"
        print(f"Changed to {self.items[self.current]}")
        print(rotary)

    def __init__(self, config):
        pinA = 17  # terminal A
        pinB = 27  # terminal B
        pinSW = 22  # switch
        glitchFilter = 300  # ms

        self.config = config

        self.pi = pigpio.pi()

        self.pi.set_mode(pinA, pigpio.INPUT)
        self.pi.set_pull_up_down(pinA, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinA, glitchFilter)

        self.pi.set_mode(pinB, pigpio.INPUT)
        self.pi.set_pull_up_down(pinB, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinB, glitchFilter)

        self.pi.set_mode(pinSW, pigpio.INPUT)
        self.pi.set_pull_up_down(pinSW, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinSW, glitchFilter)

        self.current = 0
        self.items = list(self.config.keys())

        def rotary_turned(ch, _level, _tick):
            if ch == pinA:
                levelB = self.pi.read(pinB)
                if levelB:
                    self.config[self.items[self.current]].up()  # ClockWise
                    self.turned_display(up=True)
                else:
                    self.config[self.items[self.current]].down()  # CounterClockWise
                    self.turned_display(up=False)

        def rotary_switch(ch, _level, _tick):
            if ch == pinSW:
                self.current = (self.current + 1) % len(self.config)
                self.pushed_display()

        self.pi.callback(pinA, pigpio.FALLING_EDGE, rotary_turned)
        self.pi.callback(pinSW, pigpio.FALLING_EDGE, rotary_switch)

    @property
    def current_key(self):
        return self.items[self.current]

    @property
    def current_item(self):
        return self.config[self.items[self.current]]

    def __getitem__(self, item):
        return self.config[item]

    def close(self):
        self.pi.stop()
        self.pi = None

    def __del__(self):
        if self.pi is not None:
            self.close()

    def __repr__(self):
        out = f"{self.__class__.__name__}(\n"
        for key, value in self.config.items():
            out += f"  {key} : {value}\n"
        return out + "\n)"


if __name__ == "__main__":
    import signal

    rotary = Rotary(DICT)

    while True:
        signal.pause()

    rotary.close()
