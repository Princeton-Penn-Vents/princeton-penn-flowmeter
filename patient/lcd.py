#!/usr/bin/env python3

import pigpio
import time
from typing import Union, Optional
import enum

class Align(enum.Enum):
    RIGHT = enum.auto()
    CENTER = enum.auto()
    LEFT = enum.auto()

class LCD:
    DEVICE_LCD = 0x3C  # Slave 0x78 << 1
    pinRST = 26  # Soft Reset pin GPIO26

    def __init__(self, *, pi: pigpio.pi = None):

        # Get pigio connection
        self.pi = pigpio.pi() if pi is None else pi

        # Get I2C bus handle
        self.hLCD = self.pi.i2c_open(6, self.DEVICE_LCD)
        print(self.hLCD)

        # initialize
        self.reset()  # issue soft reset to LCD
        print("LCD Reset")
        time.sleep(0.04)  # wait 40ms

        self.clear()  # Needed to fix flakiness when restarting
        self.ctrl(0x38)  # Function set - 8 bit, 2 line, norm height, inst table 0
        print("LCD Function Set")
        time.sleep(0.01)

        self.ctrl(0x39)  # Function set - 8 bit, 2 line, norm height, inst table 1
        print("LCD Function Set 2")
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

    def reset(self) -> None:
        self.pi.write(self.pinRST, 0)
        time.sleep(0.002)
        self.pi.write(self.pinRST, 1)

    def ctrl(self, value: int) -> None:
        self.pi.i2c_write_device(self.hLCD, [0x00, value])

    def text(self, text: str) -> None:
        b = text.encode("ascii")
        self.pi.i2c_write_device(self.hLCD, [0x40] + [*b])

    def upper(self, text: str, *, pos: Union[int, Align] = Align.LEFT) -> None:
        if pos == Align.LEFT:
            pos = 0
        elif pos == Align.CENTER:
            pos = (20 - len(text)) // 2
        else:
            pos = 20 - len(text)

        self.ctrl(0x80 + pos)
        self.text(text)

    def lower(self, text: str, *, pos: Union[int, Align] = Align.LEFT) -> None:
        if pos == Align.LEFT:
            pos = 0
        elif pos == Align.CENTER:
            pos = (20 - len(text)) // 2
        else:
            pos = 20 - len(text)

        self.ctrl(0xC0 + pos)
        self.text(text)

    def clear(self) -> None:
        self.ctrl(0x01)

    def close(self) -> None:
        if hasattr(self, "hLCD"):
            self.pi.i2c_close(self.hLCD)
        self.pi.stop()
        self.pi = None  # type: ignore

    def __del__(self) -> None:
        if self.pi is not None:
            self.close()


if __name__ == "__main__":
    lcd = LCD()
    lcd.upper("HELLO", pos=Align.CENTER)
    lcd.lower("WORLD", pos=Align.CENTER)
    lcd.close()
