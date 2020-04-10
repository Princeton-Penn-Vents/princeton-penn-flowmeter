from nurse.generator import Generator

import json
import threading
import zmq


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
        socket.setsockopt_string(zmq.SUBSCRIBE, "ppv1")

        while not self.signal_end.is_set():
            string = socket.recv_string()
            j = json.loads(string[5:])

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
        self._thread = CollectorThread()
        self._thread.start()

    def get_data(self):
        (self._time, self._flow, self._pressure) = self._thread.get_data()

    @property
    def time(self):
        return self._time

    @property
    def flow(self):
        return self._flow

    @property
    def pressure(self):
        return self._pressure

    @property
    def volume(self):
        return self._pressure  # CHANGE!

    def close(self):
        self._thread.signal_end.set()


if __name__ == "__main__":
    coll = Collector()
    time.sleep(5)
    coll.get_data()
    print(f"Received {len(coll.time)} values in 5 seconds")
    time.sleep(5)
    coll.get_data()
    print(f"Received {len(coll.time)} values in 10 seconds")
    coll.close()


# For full project:

# poll the device input for current values (at least every second)
# Run analysis code
# Wait for https comms and respond if asked
# (possible) changes in dial
# (possible) display LCD
# Set colors on LCD
