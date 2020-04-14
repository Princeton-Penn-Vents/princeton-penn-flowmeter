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

        self._time = Rolling(window_size=30 * 50, dtype=np.int64)
        self._flow = Rolling(window_size=30 * 50)
        self._pressure = Rolling(window_size=30 * 50)

        self._start_time = int(1000 * datetime.now().timestamp())
        (self._sim,) = start_sims(1, self._start_time, 12000000)

        self._logging = logging

    def get_data(self):
        t = int(datetime.now().timestamp() * 1000)
        root = self._sim.get_from_timestamp(t, 5000)
        time = root["data"]["timestamps"]
        flow = root["data"]["flows"]
        pressure = root["data"]["pressures"]

        to_add = new_elements(self._time, time)
        self._time.inject(time[-to_add:])
        self._flow.inject(flow[-to_add:])
        self._pressure.inject(pressure[-to_add:])

    @property
    def flow(self):
        if self.status == Status.DISCON:
            return []
        return np.asarray(self._flow) * (
            0.6 if self._force_status == Status.ALERT else 1
        )

    @property
    def pressure(self):
        if self.status == Status.DISCON:
            return []
        return np.asarray(self._pressure) * (
            0.6 if self._force_status == Status.ALERT else 1
        )

    @property
    def timestamps(self):
        if self.status != Status.DISCON and len(self._time) > 0:
            return np.asarray(self._time)
        else:
            return np.array([], dtype=np.double)
