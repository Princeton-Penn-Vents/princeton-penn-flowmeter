from datetime import datetime
import numpy as np

from processor.generator import Generator, Status
from processor.threaded_generator import RemoteThread
from typing import Optional, Dict, Any


class RemoteGenerator(Generator):
    def __init__(self, *, ip: str = "127.0.0.1", port: int = 8100):
        super().__init__()
        self.ip = ip
        self.port = port

        self._last_update: Optional[float] = None

        self.status = Status.DISCON
        self._last_ts: int = 0

        self._time = np.array([], dtype=np.int64)
        self._flow = np.array([], dtype=np.double)
        self._pressure = np.array([], dtype=np.double)

        self._remote_thread: Optional[RemoteThread] = None

    def run(self) -> None:
        super().run()
        self._remote_thread = RemoteThread(
            self, address=f"http://{self.ip}:{self.port}"
        )
        self._remote_thread.start()

    def _get_data(self) -> None:
        if self._remote_thread is not None:
            self._remote_thread.access_collected_data()

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
        super().close()
        if self._remote_thread is not None:
            self._remote_thread.join()
