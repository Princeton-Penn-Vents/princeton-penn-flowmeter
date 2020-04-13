import abc
import enum
import os

import numpy as np
from datetime import datetime

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
        self._old_realtime = None
        self._volume_unshifted_min = None
        self._volume_shift = 0.0
        self._breaths = []
        self._cumulative = {}
        self._alarms = {}
        self._rotary = patient.rotary.MockRotary(patient.rotary.DICT)
        self.last_update = None

    def set_rotary(self, rotary):
        self._rotary = rotary

    @abc.abstractmethod
    def get_data(self):
        pass

    def analyze(self):
        realtime = self.realtime

        if len(realtime) > 0:
            if getattr(self, "_logging", None):
                if os.path.exists(self._logging) and not os.path.isdir(self._logging):
                    warnings.warn("{} is not a directory; not logging".format(self._logging))
                else:
                    if not os.path.exists(self._logging):
                        os.mkdir(self._logging)
                    if self._old_realtime is None or len(self._old_realtime) == 0:
                        start_index = 0
                    else:
                        start_index = np.argmin(abs(realtime - self._old_realtime[-1])) + 1

                    with open(os.path.join(
                        self._logging, "time_{}.dat".format(id(self))
                    ), "ba") as file:
                        file.write((realtime[start_index:] * 1000).astype("<u8").tostring())

                    with open(os.path.join(
                        self._logging, "flow_{}.dat".format(id(self))
                    ), "ba") as file:
                        file.write(self.flow[start_index:].astype("<f4").tostring())

                    with open(os.path.join(
                        self._logging, "pres_{}.dat".format(id(self))
                    ), "ba") as file:
                        file.write(self.pressure[start_index:].astype("<f4").tostring())

            self._volume = nurse.analysis.flow_to_volume(
                realtime,
                self._old_realtime,
                self.flow,
                self._volume - self._volume_shift,
            )
            self._old_realtime = realtime
            if self._volume_unshifted_min is None:
                self._volume_unshifted_min = np.min(self._volume)
            else:
                self._volume_unshifted_min = min(
                    self._volume_unshifted_min, np.min(self._volume)
                )

            self._volume_shift = -self._volume_unshifted_min
            self._volume = self._volume + self._volume_shift

            breaths = nurse.analysis.measure_breaths(
                realtime, self.flow, self.volume, self.pressure
            )

            if len(breaths) > 0:
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
        tardy = 0 if self.last_update is None else (datetime.now().timestamp() - self.last_update)*1000
        if len(timestamps) > 0:
            return -(timestamps - timestamps[-1] - tardy) / 1000
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

    @property
    def cumulative(self):
        return self._cumulative

    def close(self):
        pass
