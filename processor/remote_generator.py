from __future__ import annotations

from processor.analysis import pressure_deglitch_smooth


import numpy as np
import zmq
from zmq.decorators import context, socket
import threading
import time
from datetime import datetime
from typing import Optional, Dict
import logging

from processor.rolling import Rolling, new_elements
from processor.generator import Status, Generator

logger = logging.getLogger("povm")


class RemoteThread(threading.Thread):
    def __init__(self, parent: RemoteGenerator, *, address: str):
        self.parent = parent
        self._address = address
        self.status = Status.DISCON

        self._time = Rolling(window_size=Generator.WINDOW_SIZE, dtype=np.int64)
        self._flow = Rolling(window_size=Generator.WINDOW_SIZE)
        self._pressure = Rolling(window_size=Generator.WINDOW_SIZE)

        self._remote_lock = threading.Lock()
        self._last_update: Optional[float] = None
        self._last_get: Optional[float] = None
        self.rotary_dict: Dict[str, Dict[str, float]] = {}

        super().__init__()

    @context()
    @socket(zmq.SUB)
    def run(self, _ctx: zmq.Context, sub_socket: zmq.Socket) -> None:

        sub_socket.connect(self._address)
        sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        while not self.parent._stop.is_set():
            number_events = sub_socket.poll(1 * 1000)
            for _ in range(number_events):
                self._last_update = datetime.now().timestamp()
                root = sub_socket.recv_json()
                if "rotary" in root:
                    with self._remote_lock:
                        self.rotary_dict = root["rotary"]

                if "t" in root:
                    with self._remote_lock:
                        self._time.inject(root["t"])
                        self._flow.inject(root["f"])
                        self._pressure.inject(root["p"])
                        self._last_get = time.monotonic()

                        if self.status == Status.DISCON:
                            logger.info("(Re)Connecting successful")
                            self.status = Status.OK

            if number_events == 0 and self.status != Status.DISCON:
                with self._remote_lock:
                    self.status = Status.DISCON

    def access_collected_data(self) -> None:
        with self.parent.lock, self._remote_lock:
            self.parent._last_update = self._last_update
            self.parent._last_get = self._last_get

            newel = new_elements(self.parent._time, self._time)

            self.parent._time.inject(self._time[-newel:])
            self.parent._flow.inject(self._flow[-newel:])
            self.parent._pressure.inject(self._pressure[-newel:])

            if self.status == Status.DISCON:
                self.parent.status = Status.DISCON
            elif self.parent.status == Status.DISCON:
                self.parent.status = Status.OK

            if len(self._time) > 0:
                self.parent._last_ts = self._time[-1]

            for k, v in self.rotary_dict.items():
                if k in self.parent.rotary:
                    self.parent.rotary[k].value = v["value"]


class RemoteGenerator(Generator):
    def __init__(self, *, ip: str = "127.0.0.1", port: int = 8100):
        super().__init__()
        self.ip = ip
        self.port = port

        self._last_update: Optional[float] = None

        self.status = Status.DISCON
        self._last_ts: int = 0

        self._time = Rolling(window_size=Generator.WINDOW_SIZE, dtype=np.int64)
        self._flow = Rolling(window_size=Generator.WINDOW_SIZE)
        self._pressure = Rolling(window_size=Generator.WINDOW_SIZE)

        self._remote_thread: Optional[RemoteThread] = None

    def run(self) -> None:
        super().run()
        self._remote_thread = RemoteThread(self, address=f"tcp://{self.ip}:{self.port}")
        self._remote_thread.start()

    def _get_data(self) -> None:
        if self._remote_thread is not None:
            self._remote_thread.access_collected_data()

    @property
    def flow(self) -> np.ndarray:
        return np.asarray(self._flow)

    @property
    def pressure(self) -> np.ndarray:
        return pressure_deglitch_smooth(np.asarray(self._pressure))

    @property
    def timestamps(self) -> np.ndarray:
        return np.asarray(self._time)

    def close(self) -> None:
        super().close()
        if self._remote_thread is not None:
            self._remote_thread.join()
