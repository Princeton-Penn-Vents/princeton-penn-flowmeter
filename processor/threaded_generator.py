import json
import numpy as np
import requests
import threading
import time
from datetime import datetime

import processor.analysis
from processor.rolling import Rolling, new_elements
from processor.generator import Status


class GeneratorThread(threading.Thread):
    def __init__(self, address):
        self._address = address

        self._time = Rolling(window_size=30 * 50, dtype=np.int64)
        self._flow = Rolling(window_size=30 * 50)
        self._pressure = Rolling(window_size=30 * 50)

        self._lock = threading.Lock()
        self._last_update = None

        self.signal_end = threading.Event()
        self.status = Status.DISCON

        super().__init__()

    def run(self):
        # If no valid port, don't try (disconnected)
        if self._address is None:
            return

        while not self.signal_end.is_set():
            try:
                r = requests.get(self._address)
                self._last_update = datetime.now().timestamp()
            except:
                with self._lock:
                    self.status = Status.DISCON
                time.sleep(1)
                continue
            if r.status_code != 200:
                with self._lock:
                    self.status = Status.DISCON
                time.sleep(1)
                continue

            root = json.loads(r.text)
            times = np.asarray(root["data"]["timestamps"])
            flow = np.asarray(root["data"]["flows"])
            pressure = np.asarray(root["data"]["pressures"])
            with self._lock:
                if self.status == Status.DISCON:
                    print("reconnecting")
                    self.status = Status.OK
                to_add = new_elements(self._time, times)
                self._time.inject(times[-to_add:])
                self._flow.inject(flow[-to_add:])
                self._pressure.inject(pressure[-to_add:])

            time.sleep(1)

    def get_data(self):
        with self._lock:
            return (
                self.status,
                self._last_update,
                np.asarray(self._time).copy(),
                np.asarray(self._flow).copy(),
                np.asarray(self._pressure).copy(),
            )

    def analyze(self):
        self._breaths = nurse.analysis.measure_breaths(self)