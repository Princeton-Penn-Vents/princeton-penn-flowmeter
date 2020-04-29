#!/usr/bin/env python3
import pigpio
from patient.rotary_live import LiveRotary
from processor.setting import Setting
import enum
from typing import Callable, Dict, Any, Optional, TypeVar

import logging

logger = logging.getLogger("pofm")

pinA = 17  # terminal A
pinB = 27  # terminal B
pinSW = 18  # switch


class Mode(enum.Enum):
    EDIT = enum.auto()
    ALARM = enum.auto()


T = TypeVar("T", bound="Rotary")


class Rotary(LiveRotary):
    def __init__(self, config: Dict[str, Setting], *, pi: pigpio.pi = None):
        super().__init__(config)
        self.alarm_filter: Callable[[str], bool] = lambda x: True

        self.pi: Optional[pigpio.pi] = pi

        self.pushed_in = False
        self.turns: int = 0

        self._current: int = 0

    def clockwise(self) -> None:
        self._current = (self._current + 1) % len(self.config)
        self.turned_display(up=True)

    def counterclockwise(self) -> None:
        self._current = (self._current - 1) % len(self.config)
        self.turned_display(up=False)

    def pushed_clockwise(self) -> None:
        self.value().up()
        self.pushed_turned_display(up=True)

    def pushed_counterclockwise(self) -> None:
        self.value().down()
        self.pushed_turned_display(up=False)

    def push(self) -> None:
        self.pushed_display()

    def key(self) -> str:
        return self._items[self._current]

    def value(self) -> Setting:
        return self.config[self._items[self._current]]

    def turned_display(self, up: bool) -> None:
        "Override in subclass to customize"
        dir = "up" if up else "down"
        print(f"Changed to {self.key()}")

    def pushed_turned_display(self, up: bool) -> None:
        "Override in subclass to customize"
        dir = "up" if up else "down"
        print(f"Changed {self.key()} {dir}")

    def pushed_display(self) -> None:
        "Override in subclass to customize"
        print(f"Pushed")
        print(rotary)

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

    def __enter__(self: T) -> T:
        glitchFilter = 300  # ms

        # Get pigio connection
        if self.pi is None:
            self.pi = pigpio.pi()

        self.pi.set_mode(pinA, pigpio.INPUT)
        self.pi.set_pull_up_down(pinA, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinA, glitchFilter)

        self.pi.set_mode(pinB, pigpio.INPUT)
        self.pi.set_pull_up_down(pinB, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinB, glitchFilter)

        self.pi.set_mode(pinSW, pigpio.INPUT)
        self.pi.set_pull_up_down(pinSW, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinSW, glitchFilter)

        pi = self.pi

        def rotary_turned(ch: int, _level: int, _tick: int) -> None:
            if ch == pinA:
                levelB = pi.read(pinB)
                clockwise = 1 if levelB else -1

                # If this is the first turn or we change directions, just mark direction
                if self.turns == 0 or (clockwise * self.turns < 0):
                    self.turns = clockwise
                    return

                # Same direction - increment
                self.turns += clockwise

                # If we have ticked 3 (+1 initial) notches, trigger a turn
                if abs(self.turns) > 3:

                    # Reset to same-direction beginning point
                    self.turns = clockwise

                    if self.pushed_in:
                        if levelB:
                            self.pushed_clockwise()
                        else:
                            self.pushed_counterclockwise()
                    else:
                        if levelB:
                            self.clockwise()
                        else:
                            self.counterclockwise()

        def rotary_switch(ch: int, level: int, _tick: int) -> None:
            # Allow rotations to tell if this is pushed in or out
            self.pushed_in = level == 0

            # Reset the rotary turns
            self.turns = 0

            if ch == pinSW and level == 0:  # falling edge
                self.push()

        self._rotary_turned = self.pi.callback(pinA, pigpio.FALLING_EDGE, rotary_turned)
        self._rotary_switch = self.pi.callback(pinSW, pigpio.EITHER_EDGE, rotary_switch)

        return super().__enter__()

    def __exit__(self, *exc) -> None:
        assert self.pi is not None, 'Must use "with" to use'
        self._rotary_turned.cancel()
        self._rotary_switch.cancel()

        return super().__exit__(*exc)


if __name__ == "__main__":
    import signal
    from processor.settings import get_live_settings

    with Rotary(get_live_settings()) as rotary:

        while True:
            signal.pause()
