#!/usr/bin/env python3
from __future__ import annotations

import abc
from typing import List, Dict, Union, Any, ValuesView, TypeVar, Iterable, Tuple

from processor.setting import Setting


class RotaryModeBase(abc.ABC):
    @abc.abstractmethod
    def pushed_clockwise(self):
        pass

    @abc.abstractmethod
    def pushed_counterclockwise(self):
        pass

    @abc.abstractmethod
    def clockwise(self):
        pass

    @abc.abstractmethod
    def counterclockwise(self):
        pass


class RotaryCollection(RotaryModeBase):
    def __init__(self, dictionary: Dict[str, Setting]):
        self._dict = dictionary
        self._current: int = 0
        self._items: List[str] = list(self._dict.keys())

    def clockwise(self) -> None:
        self._current = (self._current + 1) % len(self._dict)

    def counterclockwise(self) -> None:
        self._current = (self._current + 1) % len(self._dict)

    def pushed_clockwise(self) -> None:
        self.value().up()

    def pushed_counterclockwise(self) -> None:
        self.value().down()

    def key(self) -> str:
        return self._items[self._current]

    def value(self) -> Setting:
        return self._dict[self._items[self._current]]

    def values(self) -> ValuesView[Setting]:
        return self._dict.values()

    def items(self) -> Iterable[Tuple[str, Setting]]:
        return self._dict.items()

    def __getitem__(self, val: str) -> Setting:
        return self._dict[val]

    def __contains__(self, key: str) -> bool:
        return key in self._dict


T = TypeVar("T", bound="LocalRotary")


class LocalRotary:
    def __init__(self, config: Union[RotaryCollection, Dict[str, Setting]]):
        self.config = config
        self._alarms: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        "Convert config to dict"
        return {k: v.to_dict() for k, v in self.config.items()}

    @property
    def alarms(self) -> Dict[str, Dict[str, float]]:
        return self._alarms

    @alarms.setter
    def alarms(self, item: Dict[str, Dict[str, float]]):
        self._alarms = item

    def __getitem__(self, item: str):
        return self.config[item]

    def values(self) -> ValuesView[Setting]:
        return self.config.values()

    def __repr__(self) -> str:
        out = f"{self.__class__.__name__}(\n"
        for key, value in self.config.items():
            out += f"  {key} : {value}\n"
        return out + "\n)"

    def __enter__(self: T) -> T:
        return self

    def __exit__(self, *args) -> None:
        return None

    def __contains__(self, key: str):
        return key in self.config

    def external_update(self) -> None:
        "Update the display after a live setting (CurrentSetting) is changed externally"
        pass
