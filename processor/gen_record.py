from __future__ import annotations

from typing import Optional
from dataclasses import dataclass
from logging import Logger
from processor.device_names import address_to_name


@dataclass
class GenRecord:
    logger: Logger

    mac: Optional[str] = None
    _nurse_name: Optional[str] = None
    _nurse_id: Optional[str] = None
    log: str = ""

    @property
    def name(self) -> str:
        if self._nurse_name is None:
            return self.box_name
        else:
            return self._nurse_name

    @name.setter
    def name(self, value: str):
        self._nurse_name = value

    @property
    def box_name(self):
        return "<unknown>" if self.mac is None else address_to_name(self.mac).title()

    @property
    def nurse_id(self) -> str:
        return "?" if self._nurse_id is None else self._nurse_id
