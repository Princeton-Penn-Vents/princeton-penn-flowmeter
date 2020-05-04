from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from processor.generator import Generator


class Saver:
    def __init__(self, gen: Generator, filepath: Path, save_every: float = None):
        self.gen = gen
        self.filepath = filepath
        self.last_save = time.monotonic()
        self.save_every = save_every
        self._last_timestamp = 0

    def __bool__(self):
        return time.monotonic() - self.last_save > self.save_every

    def save(self) -> None:
        self.last_save = time.monotonic()


class CSVSaver(Saver):
    def __init__(self, gen: Generator, filepath: Path, save_every: float = None):
        super().__init__(gen, filepath, save_every)

    def save(self) -> None:
        pass
