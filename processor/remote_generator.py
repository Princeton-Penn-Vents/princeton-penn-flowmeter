from datetime import datetime
import numpy as np

from processor.generator import Generator, Status
from processor.threaded_generator import GeneratorThread
from typing import Optional


class RemoteGenerator(Generator):
    def __init__(self, *, ip: str = "127.0.0.1", port: int = 8100):
        super().__init__()
        self.ip = ip
        self.port = port
        self._last_update: Optional[float] = None
        self._thread = GeneratorThread(address=f"http://{ip}:{port}")
        self._thread.start()
        self.status = Status.DISCON
        self._last_ts: int = 0
        self._time: Optional[np.array] = None
        self._flow: Optional[np.array] = None
        self._pressure: Optional[np.array] = None

    def prepare(self, *, from_timestamp: Optional[float] = None):
        return super().prepare(from_timestamp=from_timestamp or self._last_ts or 0)

    def get_data(self) -> None:
        (
            status,
            self._last_update,
            self._time,
            self._flow,
            self._pressure,
            rotary,
        ) = self._thread.get_data()

        if status == Status.DISCON:
            self.status = Status.DISCON
        elif self.status == Status.DISCON:
            self.status = Status.OK

        if len(self._time) > 0:
            self._last_ts = self._time[-1]

        for k, v in rotary.items():
            if k in self.rotary:
                self.rotary[k].value = v["value"]

    @property
    def flow(self) -> np.ndarray:
        return np.asarray(self._flow)

    @property
    def pressure(self) -> np.ndarray:
        return np.asarray(self._pressure)

    @property
    def timestamps(self) -> np.ndarray:
        return np.asarray(self._time)

    def close(self) -> None:
        self._thread.signal_end.set()
