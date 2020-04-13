#!/usr/bin/env python3

import sys
import time

from processor.setting import Setting, IncrSetting, SelectionSetting

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


class LocalRotary:
    def __init__(self, config):
        self.config = config
        self.current = 0
        self.items = list(self.config.keys())

    @property
    def current_key(self):
        return self.items[self.current]

    @property
    def current_item(self):
        return self.config[self.items[self.current]]

    def __getitem__(self, item):
        return self.config[item]

    def close(self):
        pass

    def __repr__(self):
        out = f"{self.__class__.__name__}(\n"
        for key, value in self.config.items():
            out += f"  {key} : {value}\n"
        return out + "\n)"
