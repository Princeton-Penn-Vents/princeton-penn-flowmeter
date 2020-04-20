#!/usr/bin/env python3

import threading
from typing import List, Any, Dict, Union, Optional
import abc

Number = Union[float, int]


class Setting(abc.ABC):
    def __init__(self, *, name: str, unit: str = None, lcd_name: str = None):
        self._name = name
        self._lcd_name: Optional[str] = lcd_name or name
        assert (
            len(self.lcd_name) <= 16
        ), "Length of LCD names must be less than 16 chars"
        self.unit = unit
        self._lock = threading.Lock()
        self._value: Any = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def lcd_name(self) -> str:
        return self._name if self._lcd_name is None else self._lcd_name

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, val: Any):
        self._value = val

    def __str__(self) -> str:
        unit = "" if self.unit is None else f" {self.unit}"
        return f"{self.value}{unit}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self}, name={self.name})"

    def to_dict(self) -> Dict[str, Union[str, float]]:
        return {"name": self.name, "value": self.value}

    def __format__(self, format_spec: str) -> str:
        return str(self).__format__(format_spec)

    @abc.abstractmethod
    def up(self) -> bool:
        pass

    @abc.abstractmethod
    def down(self) -> bool:
        pass


class DisplaySetting(Setting):
    def __init__(
        self, value: Any, *, name: str, unit: str = None, lcd_name: str = None
    ):
        super().__init__(unit=unit, name=name, lcd_name=lcd_name)

        self._value = value

    def up(self) -> bool:
        return False

    def down(self) -> bool:
        return False


class IncrSetting(Setting):
    def __init__(
        self,
        default: Number,
        *,
        min: Number,
        max: Number,
        incr: Number,
        name: str,
        unit: str = None,
        lcd_name: str = None,
    ):
        "Note: incr should be a nice floating point number"

        super().__init__(unit=unit, name=name, lcd_name=lcd_name)

        self._min = min
        self._max = max
        self._value = default
        self._incr = incr

    def up(self) -> bool:
        "Return true if not at limit"
        with self._lock:
            if self._value < self._max:
                self._value += self._incr
                return True
            else:
                return False

    def down(self) -> bool:
        "Return true if not at limit"
        with self._lock:
            if self._value > self._min:
                self._value -= self._incr
                return True
            else:
                return False

    @property
    def value(self) -> float:
        with self._lock:
            return self._value

    @value.setter  # type: ignore
    def value(self, val: float):
        # Only used to set values remotely
        with self._lock:
            self._value = val


class SelectionSetting(Setting):
    def __init__(
        self,
        default: int,
        listing: List[Any],
        *,
        name: str,
        unit: str = None,
        lcd_name: str = None,
    ):

        super().__init__(unit=unit, name=name, lcd_name=lcd_name)

        assert (
            0 < default < len(listing)
        ), "Default must be an index into the list given"

        self._value = default
        self._listing = listing

    def up(self) -> bool:
        "Return true if not at limit"
        with self._lock:
            if self._value < len(self._listing) - 1:
                self._value += 1
                return True
            else:
                return False

    def down(self) -> bool:
        "Return true if not at limit"
        with self._lock:
            if self._value > 0:
                self._value -= 1
                return True
            else:
                return False

    @property
    def value(self) -> Any:
        with self._lock:
            return self._listing[self._value]

    @value.setter  # type: ignore
    def value(self, val: float):
        # Only used to set values remotely
        with self._lock:
            self._value = self._listing.index(val)
