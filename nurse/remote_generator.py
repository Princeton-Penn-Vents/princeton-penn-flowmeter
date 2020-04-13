from datetime import datetime
import numpy as np

from sim.rolling import Rolling, new_elements
from nurse.generator import Generator, Status
from nurse.threaded_generator import GeneratorThread


class RemoteGenerator(Generator):
    def __init__(self, *, ip="127.0.0.1", port=None):
        super().__init__()
        self._thread = GeneratorThread(address=f"http://{ip}:{port}")
        self._thread.start()
        self.status = Status.DISCON

    def get_data(self):
        (self.status, self._time, self._flow, self._pressure,) = self._thread.get_data()
        
    @property
    def flow(self):
        return np.asarray(self._flow)
        #commented out things here as to be consistent with threaded_generator.
        #return np.asarray(self._flow) if self.status is not Status.DISCON else []

    @property
    def pressure(self):
        return np.asarray(self._pressure)
        #commented out things here as to be consistent with threaded_generator.
        #return np.asarray(self._pressure) if self.status is not Status.DISCON else []

    @property
    def timestamps(self):
        return np.asarray(self._time)
        #commented out things here as to be consistent with threaded_generator.
        #if self.status != Status.DISCON and len(self._time) > 0:
        #    return np.asarray(self._time)
        #else:
        #    return np.array([], dtype=np.double)

    def close(self):
        self._thread.signal_end.set()

