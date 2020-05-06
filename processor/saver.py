from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING
from datetime import datetime
import numpy as np
import json

if TYPE_CHECKING:
    from processor.generator import Generator


class Saver:
    def __init__(self, gen: Generator, filepath: Path, save_every: float):
        self.parent = gen
        self.filepath = filepath
        self.file = open(filepath, "a")
        self.last_save = time.monotonic()
        self.save_every = save_every

    def __bool__(self) -> bool:
        return time.monotonic() - self.last_save > self.save_every

    def enter(self) -> None:
        self.file.close()
        self.file = open(self.filepath, "a")
        self.header()

    def save(self) -> None:
        self.last_save = time.monotonic()

    def close(self) -> None:
        self.file.close()

    def header(self) -> None:
        self.file.write(f"# Nursetime: {datetime.now().isoformat()}\n")


class CSVSaverTS(Saver):
    def __init__(self, gen: Generator, filepath: Path, save_every: float):
        super().__init__(gen, filepath, save_every)
        self._last_timestamp = 0

    def header(self) -> None:
        super().header()
        self.file.write("t, f, p\n")

    def save(self) -> None:
        if len(self.parent._time) < 1:
            return

        ind = np.searchsorted(self.parent._time, self._last_timestamp)

        for t, f, p in zip(
            self.parent._time[ind:],
            self.parent._flow[ind:],
            self.parent._pressure[ind:],
        ):
            self.file.write(f"{t},{f:.2},{p:.3}\n")

        self._last_timestamp = self.parent._time[-1]
        super().save()


class CSVSaverCML(Saver):
    def save(self) -> None:
        self.file.write(json.dumps(self.parent.cumulative))
        self.file.write("\n")
        super().save()


class JSONSSaverBreaths(Saver):
    def __init__(self, gen: Generator, filepath: Path):
        super().__init__(gen, filepath, 0.0)

    def __bool__(self) -> bool:
        return False

    def save(self, breaths) -> None:
        for breath in breaths:
            self.file.write(json.dumps(breath))
            self.file.write("\n")
        super().save()

    def header(self) -> None:
        pass
