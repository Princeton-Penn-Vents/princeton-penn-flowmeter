import abc
import enum
import numpy as np

import numpy as np
import scipy.integrate

import nurse.analysis
import patient.rotary


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
        self._breaths = []
        self._cumulative = {}
        self._alarms = {}
        self._rotary = patient.rotary.MockRotary(patient.rotary.DICT)

    def set_rotary(self, rotary):
        self._rotary = rotary

    @abc.abstractmethod
    def get_data(self):
        pass

    def analyze(self):
        realtime = self.realtime

        if len(realtime) > 0:
            self._volume = scipy.integrate.cumtrapz(
                self.flow * 1000, realtime / 60.0, initial=0
            )

            breaths = nurse.analysis.measure_breaths(
                realtime, self.flow, self.volume, self.pressure
            )

            self._breaths, updated, new_breaths = nurse.analysis.combine_breaths(
                self._breaths, breaths
            )

            self._cumulative = nurse.analysis.cumulative(
                self._cumulative, updated, new_breaths
            )

            self._alarms = nurse.analysis.alarms(
                self._rotary, self._alarms, updated, new_breaths, self._cumulative
            )

    @property
    def time(self):
        timestamps = self.timestamps
        if len(timestamps) > 0:
            return -(timestamps - timestamps[-1]) / 1000
        else:
            return timestamps

    @property
    def realtime(self):
        return self.timestamps / 1000

    @property
    @abc.abstractmethod
    def timestamps(self):
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

    @property
    def breaths(self):
        return self._breaths

    @property
    def alarms(self):
        return self._alarms

    def close(self):
        pass
