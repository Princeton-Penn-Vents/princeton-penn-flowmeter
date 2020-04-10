#!/usr/bin/env python3

# Allow run from outer or inner directory (should be a package...)
try:
    from patient.rotary import Rotary, DICT
    from patient.lcd import LCD
except ImportError:
    from rotary import Rotary, DICT
    from lcd import LCD


class RotaryLCD(Rotary):
    def __init__(self, config):
        super().__init__(config)

        assert "Sensor ID" in config, "A 'Sensor ID' key must be present"
        for key in config:
            assert len(key) <= 16, "Keys must be short enough to display"

        self.lcd = LCD()

    def turned_display(self, up):
        # Top display keeps ID number!
        self.lower_display()

    def pushed_display(self):
        self.upper_display()
        self.lower_display()

    def upper_display(self):
        ID = self["Sensor ID"].value
        ID_string = f"#{ID}"
        current_name = self.current_key
        string = f"{current_name:<16} {ID_string:>3}"
        assert len(string) == 20
        self.lcd.upper(string)

    def lower_display(self):
        current_item = self.current_item
        string = f"{current_item:<20}"
        assert len(string) == 20
        self.lcd.lower(string)

    def display(self):
        self.lcd.clear()
        self.upper_display()
        self.lower_display()

    def close(self):
        self.lcd.close()
        super().close()


if __name__ == "__main__":
    import time

    rotary = RotaryLCD(DICT)
    rotary.display()

    while True:
        time.sleep(1)

    rotary.close()
