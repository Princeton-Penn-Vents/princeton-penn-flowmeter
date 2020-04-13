from datetime import datetime
import numpy as np

from sim.rolling import Rolling, new_elements
from nurse.generator import Generator, Status
from nurse.threaded_generator import GeneratorThread


class RemoteGenerator(Generator):
    def __init__(self, *, ip="127.0.0.1", port=None):
        super().__init__()
        self._last_update = None
        self._thread = GeneratorThread(address=f"http://{ip}:{port}")
        self._thread.start()
        self.status = Status.DISCON

    def get_data(self):
        (self.status, self.last_update, self._time, self._flow, self._pressure,) = self._thread.get_data()
        
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

