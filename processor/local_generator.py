import time
from datetime import datetime
import numpy as np

from sim.start_sims import start_sims
from processor.rolling import Rolling, new_elements
from processor.generator import Generator, Status


class LocalGenerator(Generator):
    def __init__(self, *, i: int):
        super().__init__()
        self.rotary["Sensor ID"].value = i
        self.status = Status.OK

        self._start_time = int(1000 * time.monotonic())
        (self._sim,) = start_sims(1, self._start_time, 12000000)

    def _get_data(self):
        t = int(time.monotonic() * 1000)
        events = t - self._time[-1] if len(self._time) else self._start_time
        times, flow, pressure = self._sim.get_from_timestamp(t, events)

        to_add = new_elements(self._time, times)
        if to_add:
            self._time.inject(times[-to_add:])
            self._flow.inject(flow[-to_add:])
            self._pressure.inject(pressure[-to_add:])

        self._last_get = self._time[-1] / 1000
        self.last_update = datetime.now()

    @property
    def flow(self):
        return np.asarray(self._flow)

    @property
    def pressure(self):
        return np.asarray(self._pressure)

    @property
    def timestamps(self):
        return np.asarray(self._time)
