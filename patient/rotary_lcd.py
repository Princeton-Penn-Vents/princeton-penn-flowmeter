#!/usr/bin/env python3

try:
    from patient.rotary import Rotary, DICT
    from patient.lcd import LCD
except ImportError:
    from rotary import Rotary, DICT
    from lcd import LCD


class RotaryLCD(Rotary):
    def __init__(self, config):
        super().__init__()

        assert "Sensor ID" in config, "A 'Sensor ID' key must be present"
        for key in config:
            assert len(key) <= 16, "Keys must be short enough to display"

        self.lcd = LCD()

    def turned_display(self, up):
        self.bottom_display()

    def pushed_display(self):
        self.top_display()

    def top_display(self):
        ID = self["Sensor ID"].value
        current_name = self.listing[self.current]
        string = f"{current_name:16} #{ID}"
        assert len(string) == 20
        self.lcd.top(string)

    def bottom_display(self):
        current_item = self.config[self.listing[self.current]]
        string = f"{current_item:20}"
        assert len(string) == 20
        self.lcd.bottom(string)

    def display(self):
        self.lcd.clear()
        self.top_display()
        self.bottom_display()

    def close(self):
        self.lcd.close()
        super().close()

if __name__ == "__main__":
    import time

    rotary = RotaryLCD(DICT)

    while True:
        time.sleep(1)

    rotary.close()
    
