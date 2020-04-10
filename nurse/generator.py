import abc
import enum


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
