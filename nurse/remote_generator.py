from datetime import datetime
import numpy as np

from sim.rolling import Rolling, new_elements
from nurse.generator import Generator, Status
from nurse.threaded_generator import GeneratorThread


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
            return []


class RemoteGenerator(Generator):
    def __init__(self, *, ip="127.0.0.1", port=None):
        self._thread = GeneratorThread(address=f"http://{ip}:{port}")
        self._thread.start()
        self.status = Status.DISCON

    def get_data(self):
        (self.status, self._time, self._flow, self._pressure,) = self._thread.get_data()

    @property
    def flow(self):
        return np.asarray(self._flow) if self.status is not Status.DISCON else []

    @property
    def pressure(self):
        return np.asarray(self._pressure) if self.status is not Status.DISCON else []

    @property
    def time(self):
        if self.status is Status.DISCON:
            return []
        if len(self._time) > 0:
            # This could be datetime.now().timestamp() if clocks accurate, but oddly doesn't work on the pi. Maybe another truncation issue.
            return -((np.asarray(self._time) - self._time[-1]) / 1000)

    def close(self):
        self._thread.signal_end.set()
