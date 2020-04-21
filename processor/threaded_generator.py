import json
import numpy as np
import requests
import threading
import time
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import logging

from processor.rolling import Rolling, new_elements
from processor.generator import Status, Generator


class GeneratorThread(threading.Thread):
    def __init__(self, address: str):
        self._address = address

        self._time = Rolling(window_size=Generator.WINDOW_SIZE, dtype=np.int64)
        self._flow = Rolling(window_size=Generator.WINDOW_SIZE)
        self._pressure = Rolling(window_size=Generator.WINDOW_SIZE)

        self._lock = threading.Lock()
        self._last_update: Optional[float] = None
        self._rotary: Dict[str, Any] = {}

        self.signal_end = threading.Event()
        self.status = Status.DISCON

        super().__init__()

    def run(self) -> None:
        # If no valid port, don't try (disconnected)
        if self._address is None:
            return

        while not self.signal_end.is_set():
            try:
                r = requests.get(self._address)
                self._last_update = datetime.now().timestamp()
            except requests.ConnectionError:
                with self._lock:
                    self.status = Status.DISCON
                time.sleep(1)
                continue
            if r.status_code != 200:
                with self._lock:
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
            with self._lock:
                if self.status == Status.DISCON:
                    logging.info("(Re)Connecting successful")
                    self.status = Status.OK
                to_add = new_elements(self._time, times)
                if to_add > 0:
                    self._time.inject(times[-to_add:])
                    self._flow.inject(flow[-to_add:])
                    self._pressure.inject(pressure[-to_add:])
                self._rotary = root.get("rotary", {})

            time.sleep(0.1)

    def get_data(self) -> Tuple[Status, Optional[float], Any, Any, Any, Dict[str, Any]]:
        with self._lock:
            return (
                self.status,
                self._last_update,
                np.asarray(self._time).copy(),
                np.asarray(self._flow).copy(),
                np.asarray(self._pressure).copy(),
                self._rotary,
            )
