from datetime import datetime
import numpy as np

from sim.start_sims import start_sims
from sim.rolling import Rolling, new_elements
from nurse.generator import Generator, Status


class LocalGenerator(Generator):
    def __init__(self, status: Status):
        self.status = status

        self._time = Rolling(window_size=30 * 50, dtype=np.int64)
        self._flow = Rolling(window_size=30 * 50)
        self._pressure = Rolling(window_size=30 * 50)

        self._start_time = int(1000 * datetime.now().timestamp())
        (self._sim,) = start_sims(1, self._start_time, 12000000)

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
        return np.asarray(self._flow) * (0.6 if self.status == Status.ALERT else 1)

    @property
    def pressure(self):
        return np.asarray(self._pressure) * (0.6 if self.status == Status.ALERT else 1)

    @property
    def time(self):
        if len(self._time) > 0:
            return -(np.asarray(self._time) - self._time[-1]) / 1000
        else:
            return np.array([], dtype=np.double)

    @property
    def timestamp(self):
        if len(self._time) > 0:
            return np.asarray(self._time) / 1000
        else:
            return np.array([], dtype=np.double)
