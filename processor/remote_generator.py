from datetime import datetime
import numpy as np

from processor.rolling import Rolling, new_elements
from processor.generator import Generator, Status
from processor.threaded_generator import GeneratorThread


class RemoteGenerator(Generator):
    def __init__(self, *, ip="127.0.0.1", port=None):
        super().__init__()
        self._last_update = None
        self._thread = GeneratorThread(address=f"http://{ip}:{port}")
        self._thread.start()
        self.status = Status.DISCON
        self._last_ts = 0

    def prepare(self):
        return super().prepare(self, from_timestamp=self._last_ts or 0)

    def get_data(self):
        (
            status,
            self.last_update,
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
    def flow(self):
        return np.asarray(self._flow)

    @property
    def pressure(self):
        return np.asarray(self._pressure)

    @property
    def timestamps(self):
        return np.asarray(self._time)

    def close(self):
        self._thread.signal_end.set()
