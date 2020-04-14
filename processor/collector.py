#!/usr/bin/env python3

from processor.generator import Generator
from processor.rolling import Rolling
import numpy as np

import threading
import zmq
import time


class CollectorThread(threading.Thread):
    def __init__(self):

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
                self._flow.inject(j["F"])
                self._pressure.inject(j["P"])

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

    def _analyzer(self):
        while not self._thread.signal_end.is_set():
            time.sleep(1.0)

            self.get_data()
            self.analyze()
            self.rotary.alarms = self.alarms

    def get_data(self):
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

    def close(self):
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

# For full project:

# poll the device input for current values (at least every second)
# Run analysis code
# Wait for https comms and respond if asked
# (possible) changes in dial
# (possible) display LCD
# Set colors on LCD
