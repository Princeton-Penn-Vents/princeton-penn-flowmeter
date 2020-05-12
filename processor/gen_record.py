from __future__ import annotations

from typing import Optional, Callable
from dataclasses import dataclass
from logging import Logger
from processor.device_names import address_to_name


@dataclass
class GenRecord:
    logger: Logger

    _mac: Optional[str] = None
    _sid: int = 0

    # Nurse only, but in master class to make simpler
    _nurse_name: str = ""

    @property
    def mac(self) -> str:
        return "<unknown>" if self._mac is None else self._mac

    @mac.setter
    def mac(self, value: str):
        if self._mac is None or self._mac != value:
            self.logger.info(f"MAC addr: {self._mac}")
            self._mac = value

    @property
    def sid(self) -> int:
        return self._sid

    @sid.setter
    def sid(self, value: int):
        if self._sid != value:
            self.logger.info(f"Sensor ID: {self._sid:X}")
            self._sid = value

    @property
    def box_name(self) -> str:
        if self.mac is None:
            return "<unknown>"
        try:
            return address_to_name(self.mac).title()
        except ValueError:
            return self.mac

    @property
    def title(self) -> str:
        """
        The title to show in the dialog box. Will show box_name if unset.
        """
        return self._nurse_name

    @title.setter
    def title(self, value: str):
        if self._nurse_name is None or self._nurse_name != value:
            self.logger.info(f"Changed title to {value!r}")
            self._nurse_name = value
            self.title_changed()

    def title_changed(self) -> None:
        """
        Modify in subclasses to add special callbacks here.
        """
