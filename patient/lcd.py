#!/usr/bin/env python3

import pigpio
import time

class LCD:
    DEVICE_LCD = 0x3C  # Slave 0x78 << 1

    def __init__(self):

        # Get pigio connection
        self.pi = pigpio.pi()

        # Get I2C bus handle
        self.hLCD = self.pi.i2c_open(6, self.DEVICE_LCD)

        # initialize
        time.sleep(0.04)  # wait 40ms

        self.ctrl(0x38)  # Function set - 8 bit, 2 line, norm height, inst table 0
        time.sleep(0.01)

        self.ctrl(0x39)  # Function set - 8 bit, 2 line, norm height, inst table 1
        time.sleep(0.01)

        self.ctrl(0x14)  # Set bias 1/5
        self.ctrl(0x78)  # Set contrast low
        self.ctrl(0x5E)  # ICON display, Booster on, Contrast high
        time.sleep(0.3)

        self.ctrl(0x6D)  # Font on, Amp ratio 6
        time.sleep(0.3)

        self.ctrl(0x0C)  # Display on, Cursor off, Cursor Pos off
        self.clear()
        time.sleep(0.002)

        self.ctrl(0x06)  # Entry mode increment

    def ctrl(self, value):
        self.pi.i2c_write_device(self.hLCD, [0x00, value])

    def text(self, text):
        b = text.encode("ascii")
        self.pi.i2c_write_device(self.hLCD, [0x40] + [*b])

    def upper(self, text, *, pos=0):
        if pos is "center":
            pos = (20 - len(text)) // 2
        self.ctrl(0x80 + pos)
        self.text(text)

    def lower(self, text, *, pos=0):
        if pos is "center":
            pos = (20 - len(text)) // 2
        self.ctrl(0xC0 + pos)
        self.text(text)

    def clear(self):
        self.ctrl(0x01)

    def close(self):
        self.pi.i2c_close(self.hLCD)
        self.pi.stop()
        self.pi = None

    def __del__(self):
        if self.pi is not None:
            self.close()


if __name__ == "__main__":
    lcd = LCD()
    lcd.upper("HELLO", pos="center")
    lcd.lower("WORLD", pos="center")
    lcd.close()
