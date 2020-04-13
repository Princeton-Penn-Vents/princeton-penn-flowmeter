#!/usr/bin/env python3

import threading


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
