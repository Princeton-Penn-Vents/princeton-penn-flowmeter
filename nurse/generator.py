import abc
import enum
import json
import numpy as np
import requests
from sim.rolling import Rolling, new_elements
from sim.start_sims import start_sims
from datetime import datetime


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
    @abc.abstractmethod
    def get_data(self):
        pass

    @abc.abstractmethod
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
        t = int(datetime.now().timestamp()*1000)
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

    def analyze(self):
        pass

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
        self.ip = ip
        self.port = port
        if port is not None:
            self.status = Status.OK
        else:
            self.status = Status.DISCON

        self._time = Rolling(window_size=30 * 50)
        self._flow = Rolling(window_size=30 * 50)
        self._pressure = Rolling(window_size=30 * 50)
        self._volume = Rolling(window_size=30 * 50)

    def get_data(self):
        # If no valid port, don't try (disconnected)
        if self.port is None:
            return

        try:
            r = requests.get(f"http://{self.ip}:{self.port}")
        except requests.exceptions.ConnectionError:
            self.status = Status.DISCON
            return

        root = json.loads(r.text)
        time = np.asarray(root["data"]["timestamps"])
        flow = np.asarray(root["data"]["flows"])
        pressure = np.asarray(root["data"]["pressures"])
        volume = self._pressure

        to_add = new_elements(self._time, time)
        self._time.inject(time[-to_add:])
        self._flow.inject(flow[-to_add:])
        self._pressure.inject(pressure[-to_add:])
        self._volume.inject(volume[-to_add:])

    def analyze(self):
        pass

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
            return -(np.asarray(self._time) - self._time[-1]) / 1000
