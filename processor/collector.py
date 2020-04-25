#!/usr/bin/env python3
from __future__ import annotations

from processor.generator import Generator
from processor.rolling import Rolling
from processor.config import config
from processor.rotary import LocalRotary
import numpy as np

import threading
import zmq
import time
from typing import Optional


class CollectorThread(threading.Thread):
    def __init__(self, parent: Collector):
        self.parent = parent

        self._time_live = Rolling(window_size=Generator.WINDOW_SIZE, dtype=np.int64)
        self._flow_live = Rolling(window_size=Generator.WINDOW_SIZE)
        self._pressure_live = Rolling(window_size=Generator.WINDOW_SIZE)

        self._flow_scale = config["device"]["flow"]["scale"].as_number()
        self._flow_offset = config["device"]["flow"]["offset"].as_number()
        self._pressure_scale = config["device"]["pressure"]["scale"].as_number()
        self._pressure_offset = config["device"]["pressure"]["offset"].as_number()

        self._collector_lock = threading.Lock()

        super().__init__()

    def run(self) -> None:
        context = zmq.Context()
        socket = context.socket(zmq.SUB)

        socket.connect("tcp://localhost:5556")
        socket.setsockopt_string(zmq.SUBSCRIBE, "")

        while not self.parent._stop.is_set():
            j = socket.recv_json()

            with self._collector_lock:
                self._time_live.inject(j["t"])
                self._flow_live.inject(
                    j["F"] ** (4 / 7) * self._flow_scale - self._flow_offset
                )
                self._pressure_live.inject(
                    j["P"] * self._pressure_scale - self._pressure_offset
                )

    def access_collected_data(self) -> None:
        with self.parent.lock, self._collector_lock:
            self.parent._time = np.asarray(self._time_live).copy()
            self.parent._flow = np.asarray(self._flow_live).copy()
            self.parent._pressure = np.asarray(self._pressure_live).copy()


class Collector(Generator):
    def __init__(self, *, rotary: LocalRotary = None):
        super().__init__(rotary=rotary)

        self._time = np.array([], dtype=np.int64)
        self._flow = np.array([], dtype=np.double)
        self._pressure = np.array([], dtype=np.double)

        self._collect_thread: Optional[CollectorThread] = None

    def get_data(self) -> None:
        if self._collect_thread is not None:
            self._collect_thread.access_collected_data()

    def analyze(self) -> None:
        super().analyze()

        self.rotary.alarms = self.alarms

    def analyze_timeseries(self) -> None:
        super().analyze_timeseries()

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

    @property
    def timestamps(self):
        with self.lock:
            return self._time

    @property
    def flow(self):
        with self.lock:
            return self._flow

    @property
    def pressure(self):
        with self.lock:
            return self._pressure

    def run(self) -> None:
        super().run()
        self._collect_thread = CollectorThread(self)
        self._collect_thread.start()

    def close(self) -> None:
        super().close()
        if self._collect_thread is not None:
            self._collect_thread.join()
            self._collect_thread = None


if __name__ == "__main__":
    with Collector() as coll:

        time.sleep(5)
        with coll.lock:
            print(f"Received {len(coll.time)} values in 5 seconds")
            print(f"Analyzer length is {len(coll.volume)}")
        time.sleep(5)

        with coll.lock:
            print(f"Received {len(coll.time)} values in 10 seconds")
            print(f"Analyzer length is {len(coll.volume)}")
            print(f"Alarms: {coll.alarms}")


# Sadly, since we are not making this a full proper python package (at the moment),
# we have to do the following to run this file for testing:
# PYTHONPATH=$PWD ./patient/collector.py
