#!/usr/bin/env python3

from processor.rotary import Setting
from patient.rotary import Rotary
from patient.lcd import LCD, Align
from patient.backlight import Backlight
from patient.buzzer import Buzzer
import pigpio
from typing import Dict
import enum
import time
import uuid


class AlarmLevel(enum.Enum):
    LOUD = enum.auto()
    QUIET = enum.auto()
    OFF = enum.auto()


class RotaryLCD(Rotary):
    def __init__(self, config: Dict[str, Setting], pi: pigpio.pi = None):

        super().__init__(config, pi=pi)
        self.lcd = LCD(pi=pi)
        self.backlight = Backlight(pi=pi)
        self.buzzer = Buzzer(pi=pi)
        self.alarm_level: AlarmLevel = AlarmLevel.OFF

    def external_update(self) -> None:
        self.upper_display()
        self.lower_display()

    def __enter__(self) -> "RotaryLCD":
        self.config._current = 2  # Current Setting
        self.lcd.__enter__()
        self.backlight.__enter__()
        self.buzzer.__enter__()
        super().__enter__()

        self.backlight.white()
        self.lcd.upper("Princeton Open Vent ")
        mac_addr = uuid.getnode()
        mac_str = ":".join(
            f"{(mac_addr >> ele) & 0xff :02x}" for ele in range(40, -8, -8)
        )
        self.lcd.lower(mac_str)
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

    def push(self) -> None:
        if self.alarm_level == AlarmLevel.LOUD and self.alarms:
            self.buzzer.clear()
            self.backlight.orange()
            self.alarm_level = AlarmLevel.QUIET
        else:
            super().push()

    def pushed_turned_display(self, up: bool) -> None:
        # Top display keeps ID number!
        self.upper_display()
        self.lower_display()

    def turned_display(self, up: bool) -> None:
        # Top display keeps ID number!
        self.upper_display()
        self.lower_display()

    def alert_display(self) -> None:
        if self.alarms and self.alarm_level == AlarmLevel.OFF:
            self.backlight.red()
            self.buzzer.buzz(200)
            self.alarm_level = AlarmLevel.LOUD
        elif not self.alarms:
            self.backlight.white()
            self.buzzer.clear()
            self.alarm_level = AlarmLevel.OFF

        self.lower_display()

    def pushed_display(self) -> None:
        self.alert_display()

    def upper_display(self) -> None:
        ID = self["Sensor ID"].value
        ID_string = f"#{ID}"
        current_name = self.value().lcd_name
        if len(current_name) > 17:
            print(f"Warning: Truncating {current_name!r}")
            current_name = current_name[:17]
        string = f"{current_name:<17}{ID_string:>3}"
        self.lcd.upper(string)

    def lower_display(self) -> None:
        current_item = self.value()
        string = f"{current_item:<20}"
        if len(string) > 20:
            print(f"Warning: Truncating {string!r}")
            string = string[:20]
        if self.alarms:
            n = len(self.alarms)
            if n == 1:
                string = string[:14] + " ALARM"
            else:
                string = string[:13] + " ALARMS"

        self.lcd.lower(string)

    def display(self) -> None:
        self.lcd.clear()
        self.upper_display()
        self.lower_display()


if __name__ == "__main__":
    import time
    from processor.settings import get_live_settings

    with RotaryLCD(get_live_settings()) as rotary:
        rotary.display()

        while True:
            time.sleep(1)
