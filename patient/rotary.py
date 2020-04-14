#!/usr/bin/env python3

import pigpio
from processor.rotary import LocalRotary, DICT, RotaryCollection
import enum


class Mode(enum.Enum):
    EDIT = enum.auto()
    ALARM = enum.auto()


class Rotary(LocalRotary):
    def __init__(self, config: dict, *, pi=None):
        super().__init__(RotaryCollection(config))

        self.mode = Mode.EDIT

        pinA = 17  # terminal A
        pinB = 27  # terminal B
        pinSW = 22  # switch
        glitchFilter = 300  # ms

        self.pi = pigpio.pi() if pi is None else pi

        self.pi.set_mode(pinA, pigpio.INPUT)
        self.pi.set_pull_up_down(pinA, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinA, glitchFilter)

        self.pi.set_mode(pinB, pigpio.INPUT)
        self.pi.set_pull_up_down(pinB, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinB, glitchFilter)

        self.pi.set_mode(pinSW, pigpio.INPUT)
        self.pi.set_pull_up_down(pinSW, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinSW, glitchFilter)

        def rotary_turned(ch, _level, _tick):
            if ch == pinA:
                levelB = self.pi.read(pinB)
                if levelB:
                    self.clockwise()
                else:
                    self.counterclockwise()

        def rotary_switch(ch, _level, _tick):
            if ch == pinSW:
                self.push()

        self.pi.callback(pinA, pigpio.FALLING_EDGE, rotary_turned)
        self.pi.callback(pinSW, pigpio.FALLING_EDGE, rotary_switch)

    def turned_display(self, up: bool):
        "Override in subclass to customize"
        dir = "up" if up else "down"
        print(f"Changed {self.key()} {dir}")
        print(rotary)

    def pushed_display(self):
        "Override in subclass to customize"
        print(f"Changed to {self.key()}")
        print(rotary)

    def clockwise(self):
        if self.mode == Mode.EDIT:
            self.config.clockwise()
        self.turned_display(up=True)

    def counterclockwise(self):
        if self.mode == Mode.EDIT:
            self.config.counterclockwise()
        self.turned_display(up=False)

    def push(self):
        if self.mode == Mode.EDIT:
            self.config.push()
        else:
            self.mode = Mode.EDIT
        self.pushed_display()

    @property
    def alarms(self):
        return self._alarms

    @alarms.setter
    def alarms(self, item):
        if item != self._alarms:
            if item:
                self.mode = Mode.ALARM
                self.alert()
            else:
                self.mode = Mode.EDIT
                self.alert()

            self._alarms = item

    def alert(self):
        self.alert_display()

    def alert_display(self):
        "Override in subclass to customize"
        print(f"Toggling alert status to {self.mode.name}")

    def value(self):
        return self.config.value()

    def key(self):
        return self.config.key()

    def close(self):
        super().close()

        self.pi.stop()
        self.pi = None

    def __del__(self):
        if self.pi is not None:
            self.close()


if __name__ == "__main__":
    import signal

    rotary = Rotary(DICT)

    while True:
        signal.pause()

    rotary.close()
