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
from typing import Optional, Dict, Any
from datetime import datetime
import math


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

        pub_socket = context.socket(zmq.PUB)  # publish (broadcast)
        pub_socket.bind(f"tcp://*:{self.parent._port}")

        every = 0
        while not self.parent._stop.is_set():
            socks, *_ = zmq.select([socket], [], [], 0.1)
            for sock in socks:
                j = sock.recv_json()
                t = j["t"]
                f = (
                    math.copysign(abs(j["F"]) ** (4 / 7), j["F"]) * self._flow_scale
                    - self._flow_offset
                )
                p = j["P"] * self._pressure_scale - self._pressure_offset

                pub_socket.send_json({"t": t, "f": f, "p": p})
                every += 1
                every %= 50
                if every == 0:
                    with self.parent.lock:
                        pub_socket.send_json(self.parent.rotary.to_dict())

                with self._collector_lock:
                    self._time_live.inject(t)
                    self._flow_live.inject(f)
                    self._pressure_live.inject(p)

    def access_collected_data(self) -> None:
        with self.parent.lock, self._collector_lock:
            self.parent._time = np.asarray(self._time_live).copy()
            self.parent._flow = np.asarray(self._flow_live).copy()
            self.parent._pressure = np.asarray(self._pressure_live).copy()

    def access_partial_data(self, from_timestamp: Optional[int] = None):
        with self.parent.lock, self._collector_lock:
            if from_timestamp is None:
                window = slice(min(len(self._time_live), 50 * 5), None)
            elif from_timestamp == 0:
                window = slice(None)
            else:
                start = np.searchsorted(self._time_live, from_timestamp, side="right")
                window = slice(start, None)

            return {
                "timestamps": self._time_live[window].tolist(),
                "flows": self._flow_live[window].tolist(),
                "pressures": self._pressure_live[window].tolist(),
            }


class Collector(Generator):
    def __init__(self, *, rotary: Optional[LocalRotary] = None, port: int = 8100):
        super().__init__(rotary=rotary)

        self._time = np.array([], dtype=np.int64)
        self._flow = np.array([], dtype=np.double)
        self._pressure = np.array([], dtype=np.double)

        self._collect_thread: Optional[CollectorThread] = None
        self._port = port

        # The collector does not need the full breath analysis
        self.disable_full_analyze = True

    def _get_data(self) -> None:
        if self._collect_thread is not None:
            self._collect_thread.access_collected_data()

    def _analyze_full(self) -> None:
        super()._analyze_full()

        self.rotary.alarms = self.alarms

    def _analyze_timeseries(self) -> None:
        super()._analyze_timeseries()

        if "Current Setting" in self.rotary:
            setting = self.rotary["Current Setting"]

            F = self.average_flow
            P = self.average_pressure

            setting.from_processor(
                F=list(F.values()), P=list(P.values()),
            )
            self.rotary.external_update()

        self.rotary.alarms = self.alarms

    def prepare(self, *, from_timestamp: Optional[int] = None) -> Dict[str, Any]:
        """
        Prepare a dict for transmission via json. Does *not* call `get_data()`
        """
        if self._collect_thread is not None:
            data = self._collect_thread.access_partial_data(from_timestamp)
        else:
            data = {}

        return {
            "version": 1,
            "time": datetime.now().timestamp(),
            # "alarms": self.alarms,
            # "cumulative": self.cumulative,
            "rotary": self.rotary.to_dict(),
            "data": data,
        }

    @property
    def timestamps(self):
        return self._time

    @property
    def flow(self):
        return self._flow

    @property
    def pressure(self):
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
