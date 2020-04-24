#!/usr/bin/env python3

from processor.generator import Generator
from processor.rolling import Rolling
from processor.config import config
import numpy as np

import threading
import zmq
import time


class CollectorThread(threading.Thread):
    def __init__(self) -> None:

        self._flow_scale = config["device"]["flow"]["scale"].as_number()
        self._flow_offset = config["device"]["flow"]["offset"].as_number()
        self._pressure_scale = config["device"]["pressure"]["scale"].as_number()
        self._pressure_offset = config["device"]["pressure"]["offset"].as_number()

        self._time = Rolling(window_size=Generator.WINDOW_SIZE, dtype=np.int64)
        self._flow = Rolling(window_size=Generator.WINDOW_SIZE)
        self._pressure = Rolling(window_size=Generator.WINDOW_SIZE)

        self._lock = threading.Lock()
        self.signal_end = threading.Event()

        super().__init__()

    def run(self):

        context = zmq.Context()
        socket = context.socket(zmq.SUB)

        socket.connect("tcp://localhost:5556")
        socket.setsockopt_string(zmq.SUBSCRIBE, "")

        while not self.signal_end.is_set():
            j = socket.recv_json()

            with self._lock:
                self._time.inject(j["t"])
                self._flow.inject(j["F"] * self._flow_scale - self._flow_offset)
                self._pressure.inject(
                    j["P"] * self._pressure_scale - self._pressure_offset
                )

    def get_data(self):
        with self._lock:
            return (
                np.asarray(self._time).copy(),
                np.asarray(self._flow).copy(),
                np.asarray(self._pressure).copy(),
            )


class Collector(Generator):
    def __init__(self):
        super().__init__()

        self._time = np.array([], dtype=np.int64)
        self._flow = np.array([], dtype=np.double)
        self._pressure = np.array([], dtype=np.double)

        self._thread = CollectorThread()
        self._thread.start()

        self._analyzer_thread = threading.Thread(target=self._analyzer)
        self._analyzer_thread.start()

    def _analyzer(self) -> None:
        self._last_ana = time.monotonic()
        while not self._thread.signal_end.is_set():
            time.sleep(0.1)
            self.get_data()
            if self.analyze_as_needed():
                self.rotary.alarms = self.alarms

            if "Current Setting" in self.rotary:
                setting = self.rotary["Current Setting"]

                RR = self.cumulative_bywindow.get("RR", 0.0)
                F = self.cumulative_bywindow.get("window average flow", [0.0] * 7)
                P = self.cumulative_bywindow.get("window average pressure", [0.0] * 7)

                if isinstance(F, dict):
                    F = list(F.values())

                if isinstance(P, dict):
                    P = list(P.values())

                setting.from_processor(
                    F=F, P=P, RR=[RR] * 7,
                )
                self.rotary.external_update()

    def get_data(self) -> None:
        self._time, self._flow, self._pressure = self._thread.get_data()

    @property
    def timestamps(self):
        return self._time

    @property
    def flow(self):
        return self._flow

    @property
    def pressure(self):
        return self._pressure

    def close(self) -> None:
        self._thread.signal_end.set()
        self._thread.join()
        self._analyzer_thread.join()


if __name__ == "__main__":
    coll = Collector()
    time.sleep(5)
    coll.get_data()
    print(f"Received {len(coll.time)} values in 5 seconds")
    print(f"Analyzer length is {len(coll.volume)}")
    time.sleep(5)
    coll.get_data()
    print(f"Received {len(coll.time)} values in 10 seconds")
    print(f"Analyzer length is {len(coll.volume)}")
    print(f"Alarms: {coll.alarms}")
    coll.close()


# Sadly, since we are not making this a full proper python package (at the moment),
# we have to do the following to run this file for testing:
# PYTHONPATH=$PWD ./patient/collector.py
