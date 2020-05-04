from __future__ import annotations

from processor.analysis import pressure_deglitch_smooth


import numpy as np
import zmq
from zmq.decorators import context, socket
import threading
import time
from datetime import datetime
from typing import Optional, Dict

from processor.rolling import Rolling, new_elements
from processor.generator import Status, Generator


class RemoteThread(threading.Thread):
    def __init__(self, parent: RemoteGenerator):
        self.parent = parent
        self._address = self.parent.address
        self._address_change = threading.Event()
        self.status = Status.DISCON

        self._time = Rolling(window_size=parent.window_size, dtype=np.int64)
        self._flow = Rolling(window_size=parent.window_size)
        self._pressure = Rolling(window_size=parent.window_size)

        self._remote_lock = threading.Lock()
        self._last_update: Optional[datetime] = None
        self._last_get: Optional[float] = None
        self.rotary_dict: Dict[str, Dict[str, float]] = {}
        self.mac = ""

        super().__init__()

    def clear(self) -> None:
        self._time.clear()
        self._flow.clear()
        self._pressure.clear()
        self._last_get = None
        self._last_update = None
        self.mac = ""

    @context()
    @socket(zmq.SUB)
    def run(self, _ctx: zmq.Context, sub_socket: zmq.Socket) -> None:

        sub_socket.connect(self._address)
        sub_socket.subscribe(b"")

        while not self.parent.stop.is_set():
            # Allow changing connections
            if self._address_change.is_set():
                with self._remote_lock, self.parent.lock:
                    sub_socket.disconnect(self._address)
                    sub_socket.connect(self.parent._address)
                    self._address = self.parent._address
                    self._address_change.clear()

                    self.clear()
                    self.parent.clear()

                    self.status = self.parent.status = Status.DISCON

            number_events = sub_socket.poll(1 * 1000)
            for _ in range(number_events):
                self._last_update = datetime.now()
                root = sub_socket.recv_json()
                if "mac" in root:
                    with self._remote_lock:
                        self.mac = root["mac"]
                if "rotary" in root:
                    with self._remote_lock:
                        self.rotary_dict = root["rotary"]

                if "t" in root:
                    with self._remote_lock:
                        self._time.inject_value(root["t"])
                        self._flow.inject_value(root["f"])
                        self._pressure.inject_value(root["p"])
                        self._last_get = time.monotonic()

                        if self.status == Status.DISCON:
                            self.parent.logger.info(
                                f"(Re)Connecting to {self._address} successful"
                            )
                            self.status = Status.OK

            if number_events == 0 and self.status != Status.DISCON:
                with self._remote_lock:
                    self.status = Status.DISCON
                    self.parent.logger.info(f"Dropped connection to {self._address}")

    def access_collected_data(self) -> None:
        with self.parent.lock, self._remote_lock:
            self.parent.last_update = self._last_update
            self.parent._last_get = self._last_get

            newel = new_elements(self.parent._time, self._time)

            self.parent._time.inject(self._time[-newel:])
            self.parent._flow.inject(self._flow[-newel:])
            self.parent._pressure.inject(self._pressure[-newel:])

            if self.status == Status.DISCON:
                self.parent.status = Status.DISCON
            elif self.parent.status == Status.DISCON:
                self.parent.status = Status.OK

            self.parent.mac = self.mac

            if len(self._time) > 0:
                self.parent._last_ts = self._time[-1]

            for k, v in self.rotary_dict.items():
                if k in self.parent.rotary:
                    self.parent.rotary[k].value = v["value"]


class RemoteGenerator(Generator):
    def __init__(self, *, address: str = "tcp://127.0.0.1:8100"):
        super().__init__()
        self._address = address
        self.rotary["Sensor ID"].value = 0

        self.status = Status.DISCON
        self._last_ts: int = 0

        self._remote_thread: Optional[RemoteThread] = None

    def clear(self) -> None:
        super().clear()

        self.status = Status.DISCON
        self._last_ts = 0

    def run(self) -> None:
        super().run()
        self._remote_thread = RemoteThread(self)
        self._remote_thread.start()

    def _get_data(self) -> None:
        if self._remote_thread is not None:
            self._remote_thread.access_collected_data()

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str) -> None:
        self._address = value
        if self._remote_thread is not None:
            self._remote_thread._address_change.set()

    @property
    def pressure(self) -> np.ndarray:
        return pressure_deglitch_smooth(np.asarray(self._pressure))

    def close(self) -> None:
        super().close()
        if self._remote_thread is not None:
            self._remote_thread.join()
