from datetime import datetime
import abc
import enum
import json
import numpy as np
import requests
import threading
import time

from sim.rolling import Rolling, new_elements
from sim.start_sims import start_sims


class Status(enum.Enum):
    OK = enum.auto()
    ALERT = enum.auto()
    DISCON = enum.auto()


COLOR = {
    Status.OK: (151, 222, 121),
    Status.ALERT: (237, 67, 55),
    Status.DISCON: (50, 50, 220),
}


class GeneratorThread(threading.Thread):
    def __init__(self, address):
        self._address = address

        self._time = Rolling(window_size=30 * 50)
        self._flow = Rolling(window_size=30 * 50)
        self._pressure = Rolling(window_size=30 * 50)
        self._volume = Rolling(window_size=30 * 50)

        self._lock = threading.Lock()

        self.signal_end = threading.Event()
        self.status = Status.DISCON

        super().__init__()

    def run(self):
        # If no valid port, don't try (disconnected)
        if self._address is None:
            return

        while not self.signal_end.is_set():
            try:
                r = requests.get(self._address)
            except requests.exceptions.ConnectionError:
                with self._lock:
                    self.status = Status.DISCON
                return

            root = json.loads(r.text)
            times = np.asarray(root["data"]["timestamps"])
            flow = np.asarray(root["data"]["flows"])
            pressure = np.asarray(root["data"]["pressures"])
            volume = self._pressure

            with self._lock:
                if self.status == Status.DISCON:
                    self.status = Status.OK
                to_add = new_elements(self._time, times)
                self._time.inject(times[-to_add:])
                self._flow.inject(flow[-to_add:])
                self._pressure.inject(pressure[-to_add:])
                self._volume.inject(volume[-to_add:])

            time.sleep(1)

    def get_data(self):
        with self._lock:
            return (
                self.status,
                np.asarray(self._time).copy(),
                np.asarray(self._flow).copy(),
                np.asarray(self._pressure).copy(),
                np.asarray(self._volume).copy(),
            )


class Generator(abc.ABC):
    @abc.abstractmethod
    def get_data(self):
        pass

    def analyze(self):
        pass

    @property
    @abc.abstractmethod
    def time(self):
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
    @abc.abstractmethod
    def volume(self):
        pass

    def close(self):
        pass


class LocalGenerator(Generator):
    def __init__(self, status: Status):
        self.status = status

        self._time = Rolling(window_size=30 * 50)
        self._flow = Rolling(window_size=30 * 50)
        self._pressure = Rolling(window_size=30 * 50)
        self._volume = Rolling(window_size=30 * 50)

        self._start_time = int(1000 * datetime.now().timestamp())
        (self._sim,) = start_sims(1, self._start_time, 12000000)

    def get_data(self):
        t = int(datetime.now().timestamp() * 1000)
        root = self._sim.get_from_timestamp(t, 5000)
        time = root["data"]["timestamps"]
        flow = root["data"]["flows"]
        pressure = root["data"]["pressures"]
        volume = self._pressure

        to_add = new_elements(self._time, time)
        self._time.inject(time[-to_add:])
        self._flow.inject(flow[-to_add:])
        self._pressure.inject(pressure[-to_add:])
        self._volume.inject(volume[-to_add:])

    @property
    def flow(self):
        return np.asarray(self._flow) * (0.6 if self.status == Status.ALERT else 1)

    @property
    def volume(self):
        return np.asarray(self._volume) * (0.6 if self.status == Status.ALERT else 1)

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
        (
            self.status,
            self._time,
            self._flow,
            self._pressure,
            self._volume,
        ) = self._thread.get_data()

    @property
    def flow(self):
        return np.asarray(self._flow) if self.status is not Status.DISCON else []

    @property
    def volume(self):
        return np.asarray(self._volume) if self.status is not Status.DISCON else []

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
