#!/usr/bin/env python3
from __future__ import annotations

from processor.generator import Generator
from processor.rolling import Rolling, new_elements
from processor.config import config
from processor.rotary import LocalRotary
import numpy as np

import threading
import zmq
from zmq.decorators import context, socket
import time
from datetime import datetime
from typing import Optional
import math
import uuid

_mac_addr = uuid.getnode()
MAC_STR = ":".join(f"{(_mac_addr >> ele) & 0xff :02x}" for ele in range(40, -8, -8))


class CollectorThread(threading.Thread):
    def __init__(self, parent: Collector):
        self.parent = parent

        self._time = Rolling(window_size=Generator.WINDOW_SIZE, dtype=np.int64)
        self._flow = Rolling(window_size=Generator.WINDOW_SIZE)
        self._pressure = Rolling(window_size=Generator.WINDOW_SIZE)

        self._flow_scale = config["device"]["flow"]["scale"].as_number()
        self._flow_offset = config["device"]["flow"]["offset"].as_number()
        self._pressure_scale = config["device"]["pressure"]["scale"].as_number()
        self._pressure_offset = config["device"]["pressure"]["offset"].as_number()

        self._collector_lock = threading.Lock()

        super().__init__()

    @context()
    @socket(zmq.SUB)
    @socket(zmq.PUB)
    def run(
        self, _ctx: zmq.Context, sub_socket: zmq.Socket, pub_socket: zmq.Socket
    ) -> None:
        sub_socket.connect("tcp://localhost:5556")
        sub_socket.subscribe(b"")

        # Up to 60 seconds of data (roughly, not promised)
        pub_socket.hwm = 3000

        pub_socket.bind(f"tcp://*:{self.parent.port}")

        last = time.monotonic()
        while not self.parent.stop.is_set():
            ready_events = sub_socket.poll(0.1)
            for _ in range(ready_events):
                j = sub_socket.recv_json()
                t = j["t"]

                # Disconnected sensor block will send 0's
                if "F" not in j or "P" not in j:
                    f: float = 0
                    p: float = 0
                else:
                    f = (
                        math.copysign(abs(j["F"]) ** (4 / 7), j["F"]) * self._flow_scale
                        - self._flow_offset
                    )
                    p = j["P"] * self._pressure_scale - self._pressure_offset

                pub_socket.send_json({"t": t, "f": f, "p": p})

                with self._collector_lock:
                    self._time.inject_value(t)
                    self._flow.inject_value(f)
                    self._pressure.inject_value(p)

            # Send rotary every ~1 second, regardless of status of input
            if time.monotonic() > (last + 1) or self.parent.rotary._changed.is_set():
                with self.parent.lock:
                    pub_socket.send_json(
                        {
                            "rotary": self.parent.rotary.to_dict(),
                            "date": datetime.now().timestamp(),
                            "mac": MAC_STR,
                        }
                    )
                last = time.monotonic()
                self.parent.rotary._changed.clear()

    def access_collected_data(self) -> None:
        with self.parent.lock, self._collector_lock:
            newel = new_elements(self.parent._time, self._time)

            self.parent._time.inject(self._time[-newel:])
            self.parent._flow.inject(self._flow[-newel:])
            self.parent._pressure.inject(self._pressure[-newel:])


class Collector(Generator):
    def __init__(self, *, rotary: Optional[LocalRotary] = None, port: int = 8100):
        super().__init__(rotary=rotary)

        self._collect_thread: Optional[CollectorThread] = None
        self.port = port

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

    @property
    def pressure(self):
        return np.asarray(self._pressure)

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
