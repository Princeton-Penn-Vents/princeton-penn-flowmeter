#!/usr/bin/env python3

from processor.rotary import Setting
from patient.rotary import Rotary
from patient.lcd import LCD, Align
from patient.backlight import Backlight
from patient.buzzer import Buzzer
import pigpio
from typing import Dict
import enum


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

        assert "Sensor ID" in config, "A 'Sensor ID' key must be present"

    def external_update(self) -> None:
        self.display()

    def __enter__(self) -> "RotaryLCD":
        self.lcd.__enter__()
        self.backlight.__enter__()
        self.buzzer.__enter__()
        super().__enter__()

        self.backlight.white()
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

        super().__enter__(*exc)
        return None

    def push(self) -> None:
        if self.alarm_level == AlarmLevel.LOUD and self.alarms:
            self.buzzer.clear()
            self.backlight.orange()
            self.alarm_level = AlarmLevel.QUIET
        else:
            super().push()

    def turned_display(self, up: bool) -> None:
        # Top display keeps ID number!
        self.lower_display()

    def alert_display(self) -> None:
        if self.alarms and self.alarm_level == AlarmLevel.OFF:
            self.backlight.red()
            self.buzzer.buzz(200)
        elif not self.alarms:
            self.backlight.white()
            self.buzzer.clear()
            self.alarm_level = AlarmLevel.OFF

        self.lower_display()

    def pushed_display(self) -> None:
        self.lcd.clear()
        self.alert_display()
        self.upper_display()
        self.lower_display()

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
        self.lcd.lower(string)
        if self.alarms:
            n = len(self.alarms)
            if n == 1:
                self.lcd.lower("ALARM", Align.RIGHT)
            else:
                self.lcd.lower(f"{n} ALARMS", Align.RIGHT)

    def display(self) -> None:
        self.lcd.clear()
        self.upper_display()
        self.lower_display()


if __name__ == "__main__":
    import time
    from processor.settings import NURSE_DICT

    with RotaryLCD(NURSE_DICT) as rotary:
        rotary.display()

        while True:
            time.sleep(1)
