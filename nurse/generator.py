import abc
import enum

import scipy.integrate

import nurse.analysis

class Status(enum.Enum):
    OK = enum.auto()
    ALERT = enum.auto()
    DISCON = enum.auto()


COLOR = {
    Status.OK: (151, 222, 121),
    Status.ALERT: (237, 67, 55),
    Status.DISCON: (50, 50, 220),
}


class Generator(abc.ABC):
    def __init__(self):
        self._volume = np.array([], dtype=np.double)

    @abc.abstractmethod
    def get_data(self):
        pass

    def analyze(self):
        self._volume = scipy.integrate.cumtrapz(self.flow, self.time / 60.0, initial=0)
        self._breaths = nurse.analysis.measure_breaths(self)

    @property
    @abc.abstractmethod
    def time(self):
        pass

    @property
    @abc.abstractmethod
    def timestamp(self):
        pass

    @property
    @abc.abstractmethod
    def flow(self):
        pass

    @property
    @abc.abstractmethod
    def pressure(self):
        pass

    @property
    def volume(self):
        return self._volume

    def close(self):
        pass
