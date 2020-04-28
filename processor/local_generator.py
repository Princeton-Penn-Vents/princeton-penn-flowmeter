from datetime import datetime
import numpy as np

from sim.start_sims import start_sims
from processor.rolling import Rolling, new_elements
from processor.generator import Generator, Status


class LocalGenerator(Generator):
    def __init__(self, status: Status = Status.OK, logging=None):
        super().__init__()
        self.status = Status.OK
        self._force_status = status

        if status == Status.DISCON:
            self.status = status

        self._time = Rolling(window_size=Generator.WINDOW_SIZE, dtype=np.int64)
        self._flow = Rolling(window_size=Generator.WINDOW_SIZE)
        self._pressure = Rolling(window_size=Generator.WINDOW_SIZE)

        self._start_time = int(1000 * datetime.now().timestamp())
        (self._sim,) = start_sims(1, self._start_time, 12000000)

        self._logging = logging

    def _get_data(self):
        if self._force_status == Status.DISCON:
            return
        t = int(datetime.now().timestamp() * 1000)
        root = self._sim.get_from_timestamp(t, 5000)
        time = root["data"]["timestamps"]
        flow = root["data"]["flows"]
        pressure = root["data"]["pressures"]

        to_add = new_elements(self._time, time)
        if to_add:
            self._time.inject(time[-to_add:])
            self._flow.inject(flow[-to_add:])
            self._pressure.inject(pressure[-to_add:])

    def _analyze_full(self):
        if self._force_status == Status.DISCON:
            return
        else:
            return super()._analyze_full()

    @property
    def flow(self):
        if self._force_status == Status.DISCON:
            return []
        with self.lock:
            return np.asarray(self._flow) * (
                0.4 if self._force_status == Status.ALERT else 1
            )

    @property
    def pressure(self):
        if self._force_status == Status.DISCON:
            return []

        with self.lock:
            return np.asarray(self._pressure) * (
                0.4 if self._force_status == Status.ALERT else 1
            )

    @property
    def timestamps(self):
        if self._force_status != Status.DISCON and len(self._time) > 0:
            with self.lock:
                return np.asarray(self._time)

        return np.array([], dtype=np.double)
