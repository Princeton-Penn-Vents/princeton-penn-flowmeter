#!/usr/bin/env python3

from patient.rotary import Rotary, DICT, Mode
from patient.lcd import LCD
from patient.backlight import Backlight


class RotaryLCD(Rotary):
    def __init__(self, config):
        super().__init__(config)

        assert "Sensor ID" in config, "A 'Sensor ID' key must be present"

        self.lcd = LCD(pi=self.pi)
        self.backlight = Backlight(pi=self.pi)
        self.backlight.white()

    def turned_display(self, up):
        # Top display keeps ID number!
        self.lower_display()

    def alert_display(self):
        if self.mode == Mode.ALARM:
            self.backlight.red()
        elif self.alarms:
            self.backlight.orange()
        else:
            self.backlight.white()

    def pushed_display(self):
        self.lcd.clear()
        self.alarm_display()
        self.upper_display()
        self.lower_display()

    def upper_display(self):
        ID = self["Sensor ID"].value
        ID_string = f"#{ID}"
        current_name = self.value().lcd_name
        string = f"{current_name:<16} {ID_string:>3}"
        assert len(string) == 20, f'Too long: "{string}" > 20 chars'
        self.lcd.upper(string)

    def lower_display(self):
        current_item = self.value()
        string = f"{current_item:<20}"
        assert len(string) == 20
        self.lcd.lower(string)

    def display(self):
        self.lcd.clear()
        self.upper_display()
        self.lower_display()

    def close(self):
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
