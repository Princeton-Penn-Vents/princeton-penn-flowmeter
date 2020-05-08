#!/usr/bin/env python3
from __future__ import annotations

import pigpio
from patient.rotary_live import LiveRotary
from processor.setting import Setting
import enum
import threading
from typing import Callable, Dict, Any, Optional, TypeVar, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from typing_extensions import Final

pinA: Final[int] = 17  # terminal A
pinB: Final[int] = 27  # terminal B
pinSW: Final[int] = 18  # switch


class Mode(enum.Enum):
    EDIT = enum.auto()
    ALARM = enum.auto()


class Dir(enum.Enum):
    CLOCKWISE = 1
    COUNTERCLOCKWISE = -1


MT = TypeVar("MT", bound="MechanicalRotary")


class MechanicalRotary:
    def __init__(self, *, pi: Optional[pigpio.pi] = None):
        self.pi = pi
        self.pushed_in = False
        self.turns = 0
        self.levA = 0
        self.levB = 0
        self._last: Optional[int] = None
        self._ts = time.monotonic()
        self._filter = 0.02

    def __enter__(self: MT) -> MT:
        # Filter button pushes the normal way
        glitchFilter = 300

        # Get pigio connection
        if self.pi is None:
            self.pi = pigpio.pi()

        self.pi.set_mode(pinA, pigpio.INPUT)
        self.pi.set_pull_up_down(pinA, pigpio.PUD_UP)

        self.pi.set_mode(pinB, pigpio.INPUT)
        self.pi.set_pull_up_down(pinB, pigpio.PUD_UP)

        self.pi.set_mode(pinSW, pigpio.INPUT)
        self.pi.set_pull_up_down(pinSW, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pinSW, glitchFilter)

        self._rotary_turnedA = self.pi.callback(
            pinA, pigpio.EITHER_EDGE, self.rotary_turned
        )
        self._rotary_turnedB = self.pi.callback(
            pinB, pigpio.EITHER_EDGE, self.rotary_turned
        )
        self._rotary_switch = self.pi.callback(
            pinSW, pigpio.EITHER_EDGE, self.rotary_switch
        )

        return self

    def __exit__(self, *exc) -> None:
        assert self.pi is not None, 'Must use "with" to use'
        self._rotary_turnedA.cancel()
        self._rotary_turnedB.cancel()
        self._rotary_switch.cancel()

    def rotary_turned(self, ch: int, level: int, _tick: int) -> None:
        # Store last reading
        if ch == pinA:
            self.levA = level
        elif ch == pinB:
            self.levB = level

        # Debounce
        if self._last == ch:
            return
        self._last = ch

        # Pick the correct function to call
        if self.pushed_in:
            function = self.pushed_turn
        else:
            function = self.turn

        ts = time.monotonic()
        if level == 1 and ts > (self._ts + self._filter):
            if ch == pinA and self.levB == 1:
                self._ts = ts
                function(Dir.COUNTERCLOCKWISE)
            elif ch == pinB and self.levA == 1:
                self._ts = ts
                function(Dir.CLOCKWISE)

    def rotary_switch(self, ch: int, level: int, _tick: int) -> None:
        # Allow rotations to tell if this is pushed in or out
        self.pushed_in = level == 0

        if ch == pinSW and level == 0:  # falling edge
            self.push()

    def pushed_turn(self, dir: Dir) -> None:
        pass

    def turn(self, dir: Dir) -> None:
        pass

    def push(self) -> None:
        pass


T = TypeVar("T", bound="Rotary")


class Rotary(LiveRotary, MechanicalRotary):
    def __init__(self, config: Dict[str, Setting], *, pi: pigpio.pi = None):
        LiveRotary.__init__(self, config)
        MechanicalRotary.__init__(self, pi=pi)

        self.alarm_filter: Callable[[str], bool] = lambda x: True

        self._current: int = 0
        self._slow_turn: int = 0

        # Rate of changing screens on the display
        self._change_rate: Final[int] = 4

    def turn(self, dir: Dir) -> None:
        self._slow_turn = (self._slow_turn + dir.value) % (
            len(self.config) * self._change_rate
        )
        self._current = self._slow_turn // self._change_rate
        self.value().active()

    def pushed_turn(self, dir: Dir) -> None:
        if dir == Dir.CLOCKWISE:
            self.value().up()
        else:
            self.value().down()

        self.changed()

    def push(self) -> None:
        pass

    def key(self) -> str:
        return self._items[self._current]

    def value(self) -> Setting:
        return self.config[self._items[self._current]]

    @property
    def alarms(self) -> Dict[str, Any]:
        return {k: v for k, v in self._alarms.items() if self.alarm_filter(k)}

    @alarms.setter
    def alarms(self, item: Dict[str, Any]) -> None:
        if item != self._alarms:
            self._alarms = item
            self.alert()

    def alert(self) -> None:
        pass

    def __enter__(self: T) -> T:
        # Get pigio connection
        if self.pi is None:
            self.pi = pigpio.pi()

        LiveRotary.__enter__(self)
        MechanicalRotary.__enter__(self)
        return self

    def __exit__(self, *exc) -> None:
        LiveRotary.__exit__(self, *exc)
        MechanicalRotary.__exit__(self, *exc)


if __name__ == "__main__":

    class TestRotary(MechanicalRotary):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.turns = 0

        def pushed_turn(self, dir: Dir) -> None:
            print("PUSHED:", dir)

        def turn(self, dir: Dir) -> None:
            self.turns += dir.value
            print(self.turns)

        def push(self) -> None:
            print("Pushed")

    with TestRotary():
        forever = threading.Event()
        forever.wait()
