#!/usr/bin/env python3

from processor.generator import Generator
from processor.rolling import Rolling
import numpy as np

import threading
import zmq
import time
from typing import Optional, Dict, Any


def dig(d, key, *args, default=None):
    ret = d.get(key)
    if ret is None:
        return default
    elif not args:
        return ret
    else:
        return dig(ret, *args, default=default)


class CollectorThread(threading.Thread):
    def __init__(self, config: Optional[Dict[str, Any]]):

        self._flow_scale = dig(config, "device", "flow", "scale", default=1)
        self._flow_offset = dig(config, "device", "flow", "offset", default=0)
        self._pressure_scale = dig(config, "device", "pressure", "scale", default=1)
        self._pressure_offset = dig(config, "device", "pressure", "offset", default=0)

        self._time = Rolling(window_size=30 * 50, dtype=np.int64)
        self._flow = Rolling(window_size=30 * 50)
        self._pressure = Rolling(window_size=30 * 50)

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
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()

        self._time = np.array([], dtype=np.int64)
        self._flow = np.array([], dtype=np.double)
        self._pressure = np.array([], dtype=np.double)

        self._thread = CollectorThread(config=config)
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
                    RR = self.cumulative.get("RR", 0.0)

                    setting.from_processor(
                        F=[1.5] * 9, P=[3.5] * 9, RR=[RR] * 9,
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
