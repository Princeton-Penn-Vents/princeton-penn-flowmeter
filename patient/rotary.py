#!/usr/bin/env python3

import pigpio
from processor.rotary import LocalRotary, DICT, RotaryCollection
from processor.setting import Setting
import enum
from typing import Callable, Dict, Any


class Mode(enum.Enum):
    EDIT = enum.auto()
    ALARM = enum.auto()


class Rotary(LocalRotary):
    def __init__(self, config: dict, *, pi: pigpio.pi = None):
        super().__init__(RotaryCollection(config))
        self.config : RotaryCollection

        pinA = 17  # terminal A
        pinB = 27  # terminal B
        pinSW = 18  # switch
        glitchFilter = 300  # ms

        self.pi = pigpio.pi() if pi is None else pi
        self.alarm_filter: Callable[[str], bool] = lambda x: True

        self.pi.set_mode(pinA, pigpio.INPUT)
        self.pi.set_pull_up_down(pinA, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinA, glitchFilter)

        self.pi.set_mode(pinB, pigpio.INPUT)
        self.pi.set_pull_up_down(pinB, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinB, glitchFilter)

        self.pi.set_mode(pinSW, pigpio.INPUT)
        self.pi.set_pull_up_down(pinSW, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinSW, glitchFilter)

        def rotary_turned(ch: int, _level: int, _tick: int):
            if ch == pinA:
                levelB = self.pi.read(pinB)
                if levelB:
                    self.clockwise()
                else:
                    self.counterclockwise()

        def rotary_switch(ch:int, _level:int, _tick: int):
            if ch == pinSW:
                self.push()

        self.pi.callback(pinA, pigpio.FALLING_EDGE, rotary_turned)
        self.pi.callback(pinSW, pigpio.FALLING_EDGE, rotary_switch)

    def turned_display(self, up: bool) -> None:
        "Override in subclass to customize"
        dir = "up" if up else "down"
        print(f"Changed {self.key()} {dir}")
        print(rotary)

    def pushed_display(self) -> None:
        "Override in subclass to customize"
        print(f"Changed to {self.key()}")
        print(rotary)

    def clockwise(self) -> None:
        self.config.clockwise()
        self.turned_display(up=True)

    def counterclockwise(self) -> None:
        self.config.counterclockwise()
        self.turned_display(up=False)

    def push(self) -> None:
        self.config.push()
        self.pushed_display()

    @property
    def alarms(self) -> Dict[str, Any]:
        return {k: v for k, v in self._alarms.items() if self.alarm_filter(k)}

    @alarms.setter
    def alarms(self, item: Dict[str, Any]) -> None:
        if item != self._alarms:
            self._alarms = item
            self.alert()

    def alert(self) -> None:
        self.alert_display()

    def alert_display(self) -> None:
        "Override in subclass to customize"
        print(f"Displaying alert status")

    def value(self) -> Setting:
        return self.config.value()

    def key(self) -> str:
        return self.config.key()

    def close(self) -> None:
        super().close()

        self.pi.stop()
        self.pi = None # type: ignore

    def __del__(self) -> None:
        if self.pi is not None:
            self.close()


if __name__ == "__main__":
    import signal

    rotary = Rotary(DICT)

    while True:
        signal.pause()

    rotary.close()
