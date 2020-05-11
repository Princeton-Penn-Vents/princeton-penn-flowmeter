#!/usr/bin/env python3
from __future__ import annotations

from processor.setting import Setting
from processor.display_settings import ResetSetting, AdvancedSetting, CurrentSetting
from patient.mac_address import get_mac_addr
from processor.device_names import address_to_name
from patient.rotary import Rotary, Dir
from patient.lcd import LCD
from patient.backlight import Backlight
from patient.buzzer import Buzzer
from processor.config import config as _config

import pigpio
from typing import Dict
import enum
import time
import threading


class AlarmLevel(enum.Enum):
    LOUD = enum.auto()
    QUIET = enum.auto()
    OFF = enum.auto()


class RotaryLCD(Rotary):
    def __init__(self, config: Dict[str, Setting], pi: pigpio.pi = None):
        super().__init__(config, pi=pi)

        shade = _config["patient"]["brightness"].get(int)

        self.lcd = LCD(pi=pi)
        self.backlight = Backlight(shade=shade, pi=pi)
        self.buzzer = Buzzer(pi=pi)
        self.alarm_level: AlarmLevel = AlarmLevel.OFF
        self.buzzer_volume: int = _config["patient"]["buzzer-volume"].get(int)
        self.lock = threading.Lock()

    def external_update(self) -> None:
        if isinstance(self.value(), CurrentSetting):
            with self.lock:
                self.upper_display()
                self.lower_display()

    def __enter__(self) -> RotaryLCD:
        self.lcd.__enter__()
        self.backlight.__enter__()
        self.buzzer.__enter__()
        super().__enter__()

        self.backlight.white()
        self.lcd.upper("POVM Box name:")
        self.lcd.lower("Getting name...")
        self.lcd.lower(address_to_name(get_mac_addr()).title() + " ")
        time.sleep(3.5)
        return self

    def __exit__(self, *exc) -> None:
        self.backlight.cyan()
        self.lcd.clear()
        self.lcd.upper("Princeton Open Vent")
        self.lcd.lower("Patient loop closed")

        super().__exit__(*exc)
        self.buzzer.__exit__(*exc)
        self.backlight.__exit__(*exc)
        self.lcd.__exit__(*exc)

        if self.pi is not None:
            self.pi.stop()
            self.pi = None

    def reset(self):
        for key, item in self.config.items():
            item.reset()

    def push(self) -> None:
        if self.alarm_level == AlarmLevel.LOUD and self.alarms:
            self.buzzer.clear()
            self.backlight.orange()
            self.alarm_level = AlarmLevel.QUIET
        else:
            self.alert()
            super().push()

    def pushed_turn(self, dir: Dir) -> None:
        with self.lock:
            # Top display keeps ID number!
            super().pushed_turn(dir)
            value = self.value()
            if isinstance(value, ResetSetting) and value.at_maximum():
                self.reset()
            if value.STATIC_UPPER:
                self.upper_display()
            self.lower_display()

    def turn(self, dir: Dir) -> None:
        super().turn(dir)
        with self.lock:
            self.lower_display()
            self.upper_display()

    def alert(self) -> None:
        with self.lock:
            if self.alarms and self.alarm_level == AlarmLevel.OFF:
                self.backlight.red()
                self.buzzer.buzz(self.buzzer_volume)
                self.alarm_level = AlarmLevel.LOUD
            elif not self.alarms:
                self.backlight.white()
                self.buzzer.clear()
                self.alarm_level = AlarmLevel.OFF

            if isinstance(self.value(), AdvancedSetting):
                self.upper_display()
            else:
                self.lower_display()

        super().alert()

    def upper_display(self) -> None:
        current_name = self.value().lcd_name
        current_number = f"{self._current + 1:>2}"
        if isinstance(self.value(), AdvancedSetting):
            current_number += chr(ord("a") + self.value()._value % 26)
        length_available = 20 - len(current_number) - 2
        if len(current_name) > length_available:
            print(f"Warning: Truncating {current_name!r}")
            current_name = current_name[:length_available]

        string = f"{current_number}: {current_name:<{length_available}}"

        if self.alarms and isinstance(self.value(), AdvancedSetting):
            n = len(self.alarms)
            if n == 1:
                string = string[:14] + " ALARM"
            else:
                string = string[:13] + " ALARMS"

        self.lcd.upper(string)

    def lower_display(self) -> None:
        current_item = self.value()
        string = f"{current_item:<20}"
        if len(string) > 20:
            print(f"Warning: Truncating {string!r}")
            string = string[:20]
        if self.alarms and not isinstance(self.value(), AdvancedSetting):
            n = len(self.alarms)
            if n == 1:
                string = string[:14] + " ALARM"
            else:
                string = string[:13] + " ALARMS"

        self.lcd.lower(string)

    def display(self) -> None:
        with self.lock:
            self.lcd.clear()
            self.lower_display()
            self.upper_display()


if __name__ == "__main__":
    from processor.settings import get_live_settings

    with RotaryLCD(get_live_settings()) as rotary:
        rotary.display()

        while True:
            time.sleep(1)
