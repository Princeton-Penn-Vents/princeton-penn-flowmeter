#!/usr/bin/env python3

import pigpio
from processor.rotary import LocalRotary, DICT


class Rotary(LocalRotary):
    def turned_display(self, up):
        "Override in subclass to customize"
        dir = "up" if up else "down"
        print(f"Changed {self.items[self.current]} {dir}")
        print(rotary)

    def pushed_display(self):
        "Override in subclass to customize"
        print(f"Changed to {self.items[self.current]}")
        print(rotary)

    def __init__(self, config, *, pi=None):
        super().__init__(config)

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
                    self.config[self.items[self.current]].up()  # ClockWise
                    self.turned_display(up=True)
                else:
                    self.config[self.items[self.current]].down()  # CounterClockWise
                    self.turned_display(up=False)

        def rotary_switch(ch, _level, _tick):
            if ch == pinSW:
                self.current = (self.current + 1) % len(self.config)
                self.pushed_display()

        self.pi.callback(pinA, pigpio.FALLING_EDGE, rotary_turned)
        self.pi.callback(pinSW, pigpio.FALLING_EDGE, rotary_switch)

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
