import abc
import enum
import json
import numpy as np
import requests
from sim.rolling import Rolling, new_elements


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
        self.current = 0
        ramp = np.array(
            [0.1, 0.8807970779778823, 0.96, 0.9975273768433653, 0.9996646498695336]
        )
        decay = -1.0 * np.exp(-1.0 * np.arange(0, 3, 0.03))
        breath = 10 * np.concatenate(
            (ramp, np.full(35, 1), np.flip(ramp), -1.0 * ramp, decay)
        )
        self._flow = np.concatenate((breath, breath, breath, breath, breath, breath))
        self._flow = self._flow * np.random.uniform(0.98, 1.02, len(self._flow))
        self._time = np.arange(0, len(self._flow), 1)
        self.axistime = np.flip(self._time / 50)  # ticks per second
        # Ramp up to 500ml in 50 ticks, then simple ramp down in 100
        tvolume = np.concatenate((10 * np.arange(0, 50, 1), 5 * np.arange(100, 0, -1)))
        self._volume = np.concatenate(
            (tvolume, tvolume, tvolume, tvolume, tvolume, tvolume)
        )
        self._volume = self._volume * np.random.uniform(0.98, 1.02, len(self._volume))

    def get_data(self):
        self.current += 10
        self._flow = np.roll(self._flow, -10)
        self._volume = np.roll(self._volume, -10)

    def analyze(self):
        pass

    @property
    def flow(self):
        return self._flow * (0.6 if self.status == Status.ALERT else 1)

    @property
    def volume(self):
        return self._volume * (0.6 if self.status == Status.ALERT else 1)

    @property
    def pressure(self):
        return self._volume * (0.6 if self.status == Status.ALERT else 1)

    @property
    def time(self):
        return self.axistime


class RemoteGenerator(Generator):
    def __init__(self, *, ip="127.0.0.1", port=None):
        self.ip = ip
        self.port = port
        if port is not None:
            self.status = Status.OK
        else:
            self.status = Status.DISCON

        self._time = Rolling(window_size=30*50)
        self._flow = Rolling(window_size=30*50)
        self._pressure= Rolling(window_size=30*50)
        self._volume= Rolling(window_size=30*50)

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
            print(self._time)
            return (np.asarray(self._time) - self._time[-1]) / 1000
