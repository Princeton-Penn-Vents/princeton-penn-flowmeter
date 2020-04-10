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

    def __repr__(self):
        unit = "" if self.unit is None else f" {self.unit}"
        return f"{self.__class__.__name__}({self.value}{unit})"


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

    def __init__(self, d):
        pinA = 17  # terminal A
        pinB = 27  # terminal B
        pinSW = 22  # switch
        glitchFilter1 = 1  # 1 ms
        glitchFilter10 = 10  # 10 ms

        self.dict = d

        pi = pigpio.pi()
        pi.set_mode(pinA, pigpio.INPUT)
        pi.set_pull_up_down(pinA, pigpio.PUD_UP)
        pi.set_glitch_filter(pinA, glitchFilter1)
        pi.set_mode(pinB, pigpio.INPUT)
        pi.set_pull_up_down(pinB, pigpio.PUD_UP)
        pi.set_glitch_filter(pinB, glitchFilter1)
        pi.set_mode(pinSW, pigpio.INPUT)
        pi.set_pull_up_down(pinSW, pigpio.PUD_UP)
        pi.set_glitch_filter(pinSW, glitchFilter10)

        self.pi = pi
        self.current = 0
        self.items = list(self.dict.keys())

        def rotary_turned(ch, _level, _tick):
            if ch == pinA:
                levelB = pi.read(pinB)
                if levelB:
                    self.dict[self.items[self.current]].up()  # ClockWise
                else:
                    self.dict[self.items[self.current]].down()  # CounterClockWise
            print(f"Changed {self.items[self.current]}")
            print(rotary)

        def rotary_switch(ch, _level, _tick):
            if ch == pinSW:
                self.current = (self.current + 1) % len(self.dict)
            print(f"Changed to {self.items[self.current]}")
            print(rotary)

        pi.callback(pinA, pigpio.FALLING_EDGE, rotary_turned)
        pi.callback(pinSW, pigpio.FALLING_EDGE, rotary_switch)

    def __getitem__(self, item):
        return self.dict[item]

    def close(self):
        self.pi.stop()
        self.pi = None

    def __del__(self):
        if self.pi is not None:
            self.pi.stop()

    def __repr__(self):
        out = f"{self.__class__.__name__}(\n"
        for key, value in self.dict.items():
            out += f"  {key} : {value}\n"
        return out + "\n)"


if __name__ == "__main__":
    import signal

    rotary = Rotary(DICT)

    while True:
        signal.pause()

    rotary.close()
