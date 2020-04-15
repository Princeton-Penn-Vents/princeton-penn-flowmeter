#!/usr/bin/env python3

from processor.rotary import Setting
from patient.rotary import Rotary, DICT
from patient.lcd import LCD, Align
from patient.backlight import Backlight
import pigpio
from typing import Dict


class RotaryLCD(Rotary):
    def __init__(self, config: Dict[str, Setting]):
        pi = pigpio.pi()

        self.lcd = LCD(pi=self.pi)
        self.backlight = Backlight(pi=self.pi)
        self.backlight.white()

        super().__init__(config, pi=pi)

        assert "Sensor ID" in config, "A 'Sensor ID' key must be present"

    def turned_display(self, up: bool) -> None:
        # Top display keeps ID number!
        self.lower_display()

    def alert_display(self) -> None:
        if self.alarms:
            self.backlight.red()
        else:
            self.backlight.white()
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
        string = f"{current_name:<16} {ID_string:>3}"
        assert len(string) == 20, f'Too long: "{string}" > 20 chars'
        self.lcd.upper(string)

    def lower_display(self) -> None:
        current_item = self.value()
        string = f"{current_item:<20}"
        assert len(string) == 20
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

    def close(self) -> None:
        self.backlight.cyan()
        self.lcd.clear()
        self.lcd.upper("Princeton Open Vent")
        self.lcd.lower("Patient loop closed")
        self.lcd.close()
        super().close()


if __name__ == "__main__":
    import time

    rotary = RotaryLCD(DICT)
    rotary.display()

    while True:
        time.sleep(1)

    rotary.close()
