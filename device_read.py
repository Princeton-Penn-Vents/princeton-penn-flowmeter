#!/usr/bin/env python3

import numpy as np
import zmq

from processor.rolling import Rolling

max_pressure_roll = Rolling(window_size=1000 // 50)
pressure_roll = Rolling(window_size=1000)
flow_roll = Rolling(window_size=1000)
time_roll = Rolling(window_size=1000, dtype=np.int64)

context = zmq.Context()
socket = context.socket(zmq.SUB)

print("Collecting data")
socket.connect("tcp://localhost:5556")

socket.setsockopt_string(zmq.SUBSCRIBE, "")


for i in range(100):

    j = socket.recv_json()
    print(f"Received: {j}")

    if "max_pressure" in j:
        max_pressure_roll.inject(j["max_pressure"])

    pressure_roll.inject(j["P"])
    flow_roll.inject(j["F"])
    time_roll.inject(j["t"])


print(max_pressure_roll)
print(pressure_roll)
print(time_roll)
print(flow_roll)
