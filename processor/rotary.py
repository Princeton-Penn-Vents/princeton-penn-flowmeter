#!/usr/bin/env python3

import sys
import time
import abc
from typing import List, Dict, Union, Any

from processor.setting import Setting, IncrSetting, SelectionSetting

DICT = {
    "PIP Max": IncrSetting(30, min=0, max=40, incr=1, unit="cm-H2O", name="PIP Max"),
    "PIP Min": IncrSetting(5, min=0, max=20, incr=1, unit="cm-H2O", name="PIP Min"),
    "PEEP Max": IncrSetting(8, min=0, max=15, incr=1, unit="cm-H2O", name="PEEP Max"),
    "PEEP Min": IncrSetting(0, min=0, max=15, incr=1, unit="cm-H2O", name="PEEP Min"),
    "TVe Max": IncrSetting(700, min=100, max=1000, incr=50, unit="ml", name="TVe Max"),
    "TVe Min": IncrSetting(300, min=100, max=1000, incr=50, unit="ml", name="TVe Min"),
    "TVi Max": IncrSetting(700, min=100, max=1000, incr=50, unit="ml", name="TVi Max"),
    "TVi Min": IncrSetting(300, min=100, max=1000, incr=50, unit="ml", name="TVi Min"),
    "AvgWindow": SelectionSetting(2, [10, 15, 30, 60], unit="sec", name="AvgWindow"),
    "Alarm Reset": SelectionSetting(
        2, [10, 15, 30, 60], unit="sec", name="Alarm Reset"
    ),
    "Sensor ID": IncrSetting(1, min=1, max=20, incr=1, name="Sensor ID"),  # REQUIRED
    "Stale Data Timeout": IncrSetting(
        8,
        min=1,
        max=20,
        incr=1,
        unit="sec",
        name="Stale Data Timeout",
        lcd_name="StaleDataTimeout",
    ),
}


class RotaryModeBase(abc.ABC):
    @abc.abstractmethod
    def push(self):
        pass

    @abc.abstractmethod
    def clockwise(self):
        pass

    @abc.abstractmethod
    def counterclockwise(self):
        pass


class RotaryCollection(RotaryModeBase):
    def __init__(self, dictionary):
        self._dict = dictionary
        self._current = 0
        self._items: List[str] = list(self._dict.keys())

    def push(self):
        self.current = (self.current + 1) % len(self.config)

    def clockwise(self):
        self.value().up()

    def counterclockwise(self):
        self.value().down()

    def key(self) -> str:
        return self._items[self._current]

    def value(self) -> Setting:
        return self._dict[self._items[self._current]]

    def items(self):
        return self._config.items()

    def __getitem__(self, val):
        return self[val]


class LocalRotary:
    def __init__(self, config: Union[RotaryCollection, Dict[str, Setting]]):
        self._config = config
        self._alarms: Dict[str, Any] = {}

    @property
    def alarms(self):
        return self._alarms

    @alarms.setter
    def alarms(self, item):
        self._alarms = item

    def __getitem__(self, item: str):
        return self._config[item]

    def close(self):
        pass

    def __repr__(self):
        out = f"{self.__class__.__name__}(\n"
        for key, value in self._config.items():
            out += f"  {key} : {value}\n"
        return out + "\n)"
