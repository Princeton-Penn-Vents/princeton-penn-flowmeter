from __future__ import annotations

import json
import numpy as np
import requests
import threading
import time
from datetime import datetime
from typing import Optional, TYPE_CHECKING, Dict
import logging

from processor.rolling import Rolling, new_elements
from processor.generator import Status, Generator

if TYPE_CHECKING:
    from processor.remote_generator import RemoteGenerator


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
        # If no valid port, don't try (disconnected)
        if self._address is None:
            return

        with requests.Session() as s:
            while not self.parent._stop.is_set():
                try:
                    r = s.get(self._address)
                    self._last_update = datetime.now().timestamp()
                except requests.ConnectionError:
                    with self._remote_lock:
                        self.status = Status.DISCON
                    time.sleep(1)
                    continue
                if r.status_code != 200:
                    with self._remote_lock:
                        self.status = Status.DISCON
                    time.sleep(1)
                    continue

                try:
                    root = json.loads(r.text)
                except json.JSONDecodeError:
                    logging.warning(f"Failed to read json, trying again", exc_info=True)
                    time.sleep(0.01)
                    continue

                times = np.asarray(root["data"]["timestamps"])
                flow = np.asarray(root["data"]["flows"])
                pressure = np.asarray(root["data"]["pressures"])

                with self._remote_lock:
                    if self.status == Status.DISCON:
                        logging.info("(Re)Connecting successful")
                        self.status = Status.OK
                    to_add = new_elements(self._time, times)

                    if to_add > 0:
                        self._time.inject(times[-to_add:])
                        self._flow.inject(flow[-to_add:])
                        self._pressure.inject(pressure[-to_add:])
                        self._last_get = time.monotonic()
                    self.rotary_dict = root.get("rotary", {})

                time.sleep(0.2)

    def access_collected_data(self) -> None:
        with self.parent.lock, self._remote_lock:
            self.parent._last_update = self._last_update
            self.parent._last_get = self._last_get
            self.parent._time = np.asarray(self._time).copy()
            self.parent._flow = np.asarray(self._flow).copy()
            self.parent._pressure = np.asarray(self._pressure).copy()

            if self.status == Status.DISCON:
                self.parent.status = Status.DISCON
            elif self.status == Status.DISCON:
                self.parent.status = Status.OK

            if len(self._time) > 0:
                self.parent._last_ts = self._time[-1]

            for k, v in self.rotary_dict.items():
                if k in self.parent.rotary:
                    self.parent.rotary[k].value = v["value"]
