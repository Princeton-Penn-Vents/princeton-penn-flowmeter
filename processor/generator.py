import abc
import enum
import os
import threading
import time
import warnings

import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

import processor.analysis
import processor.rotary
from processor.settings import NURSE_DICT


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
    WINDOW_SIZE = 50 * 30  # 50 hz * 30 seconds

    def __init__(self) -> None:
        self._volume = np.array([], dtype=np.double)
        self._old_realtime = None
        self._volume_unshifted_min: Optional[Any] = None
        self._volume_shift = 0.0
        self._time_window = None
        self._flow_window = None
        self._pressure_window = None
        self._window_cumulative: Dict[str, Dict[str, Dict[int, float]]] = {
            "numer": {
                "flow": {1: 0.0, 3: 0.0, 5: 0.0, 10: 0.0, 20: 0.0, 30: 0.0, 60: 0.0},
                "pressure": {
                    1: 0.0,
                    3: 0.0,
                    5: 0.0,
                    10: 0.0,
                    20: 0.0,
                    30: 0.0,
                    60: 0.0,
                },
            },
            "denom": {"flow": {}, "pressure": {},},  # will be filled in from above
        }
        self._breaths: List[Any] = []
        self._cumulative: Dict[str, Any] = {}
        self._cumulative_timestamps: Dict[str, Any] = {}
        self._alarms: Dict[str, Any] = {}
        self.rotary = processor.rotary.LocalRotary(NURSE_DICT)
        self.last_update = None
        self.analyze_every = 2  # seconds
        self._last_ana = time.monotonic()
        self.status: Status
        self._logging: Union[str, Path]
        self.lock = threading.Lock()

    def analyze_as_needed(self) -> bool:
        if time.monotonic() - self._last_ana < self.analyze_every:
            self.analyze_timeseries()
            return False
        else:
            self.analyze()
            self._last_ana = time.monotonic()
            return True

    @abc.abstractmethod
    def get_data(self):
        pass

    def prepare(self, *, from_timestamp=None) -> Dict[str, Any]:
        if from_timestamp is None:
            window = slice(min(len(self.timestamps), 50 * 5), None)
        elif from_timestamp == 0:
            window = slice(None)
        else:
            start = np.searchsorted(self.timestamps, from_timestamp, side="right")
            window = slice(start, None)

        return {
            "version": 1,
            "time": datetime.now().timestamp(),
            "alarms": self.alarms,
            "cumulative": self.cumulative,
            "rotary": self.rotary.to_dict(),
            "data": {
                "timestamps": self.timestamps[window].tolist(),
                "flows": self.flow[window].tolist(),
                "pressures": self.pressure[window].tolist(),
            },
        }

    def analyze_timeseries(self) -> None:
        realtime = self.realtime
        if len(realtime) > 0:
            if getattr(self, "_logging", None):
                if os.path.exists(self._logging) and not os.path.isdir(self._logging):
                    warnings.warn(
                        "{} is not a directory; not logging".format(self._logging)
                    )
                else:
                    if not os.path.exists(self._logging):
                        os.mkdir(self._logging)
                    if self._old_realtime is None or len(self._old_realtime) == 0:
                        start_index = 0
                    else:
                        start_index = (
                            np.argmin(abs(realtime - self._old_realtime[-1])) + 1
                        )

                    with open(
                        os.path.join(self._logging, "time_{}.dat".format(id(self))),
                        "ba",
                    ) as file:
                        file.write(
                            (realtime[start_index:] * 1000).astype("<u8").tostring()
                        )

                    with open(
                        os.path.join(self._logging, "flow_{}.dat".format(id(self))),
                        "ba",
                    ) as file:
                        file.write(self.flow[start_index:].astype("<f4").tostring())

                    with open(
                        os.path.join(self._logging, "pres_{}.dat".format(id(self))),
                        "ba",
                    ) as file:
                        file.write(self.pressure[start_index:].astype("<f4").tostring())

            (
                self._time_window,
                self._flow_window,
                self._pressure_window,
                self._window_cumulative,
            ) = processor.analysis.window_averages(
                realtime,
                self._old_realtime,
                self.flow,
                self.pressure,
                self._time_window,
                self._flow_window,
                self._pressure_window,
                self._window_cumulative,
            )

            self._volume = processor.analysis.flow_to_volume(
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

    def analyze(self) -> None:
        self.analyze_timeseries()

        realtime = self.realtime
        alarms = self._alarms

        updated = []
        new_breaths = []
        updated_fields = set()

        if len(realtime) > 0:
            breaths = processor.analysis.measure_breaths(
                realtime, self.flow, self.volume, self.pressure
            )

            if len(breaths) > 0:
                (
                    self._breaths,
                    updated,
                    new_breaths,
                ) = processor.analysis.combine_breaths(self._breaths, breaths)

                self._cumulative, updated_fields = processor.analysis.cumulative(
                    self._cumulative, updated, new_breaths
                )

        self._cumulative, updated_fields = processor.analysis.cumulative_by_window(
            self._window_cumulative, self._cumulative, updated_fields,
        )

        self._alarms = processor.analysis.add_alarms(
            self.rotary, updated, new_breaths, self._cumulative
        )

        timestamp = time.time()
        cumulative_timestamps = dict(self._cumulative_timestamps)
        cumulative_timestamps[""] = timestamp
        for field in updated_fields:
            cumulative_timestamps[field] = timestamp
        self._cumulative_timestamps = cumulative_timestamps

        stale_threshold = self.rotary["Stale Data Timeout"].value
        default = timestamp - stale_threshold
        stale = {}
        for field in self._cumulative:
            last_update_timediff = timestamp - self._cumulative_timestamps.get(
                field, default
            )
            if last_update_timediff >= stale_threshold:
                stale[field] = last_update_timediff
        if len(stale) > 0:
            self._alarms["Stale Data"] = stale

        if hasattr(self, "status"):
            if self.alarms and self.status == Status.OK:
                self.status = Status.ALERT
            elif not self.alarms and self.status == Status.ALERT:
                self.status = Status.OK

    @property
    def time(self):
        timestamps = self.timestamps
        tardy = (
            0
            if self.last_update is None
            else (datetime.now().timestamp() - self.last_update) * 1000
        )
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

    @property
    def cumulative_timestamps(self):
        return self._cumulative_timestamps

    def close(self):
        pass
