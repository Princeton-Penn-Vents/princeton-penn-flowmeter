from __future__ import annotations

import numpy as np
import zmq
import threading
import time
from datetime import datetime
from typing import Optional, TYPE_CHECKING, Dict
import logging

from processor.rolling import Rolling, new_elements
from processor.generator import Status, Generator

if TYPE_CHECKING:
    from processor.remote_generator import RemoteGenerator

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

    def run(self) -> None:
        context = zmq.Context()
        socket = context.socket(zmq.SUB)

        socket.connect(self._address)
        socket.setsockopt_string(zmq.SUBSCRIBE, "")

        while not self.parent._stop.is_set():
            socks, *_ = zmq.select([socket], [], [], 0.1)
            for sock in socks:
                self._last_update = datetime.now().timestamp()
                root = sock.recv_json()
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

    def access_collected_data(self) -> None:
        with self.parent.lock, self._remote_lock:
            self.parent._last_update = self._last_update
            self.parent._last_get = self._last_get
            self.parent._time = np.asarray(self._time).copy()
            self.parent._flow = np.asarray(self._flow).copy()
            self.parent._pressure = np.asarray(self._pressure).copy()

            if self.status == Status.DISCON:
                self.parent.status = Status.DISCON
            elif self.parent.status == Status.DISCON:
                self.parent.status = Status.OK

            if len(self._time) > 0:
                self.parent._last_ts = self._time[-1]

            for k, v in self.rotary_dict.items():
                if k in self.parent.rotary:
                    self.parent.rotary[k].value = v["value"]
