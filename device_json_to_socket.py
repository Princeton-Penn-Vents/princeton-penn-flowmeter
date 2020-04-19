#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input single-line json file")
parser.add_argument(
    "--repeat", default=1, type=int, help="Number of times to repeat, 0 for forever"
)
args = parser.parse_args()

import zmq
import contextlib
import time

context = zmq.Context()
socket = context.socket(zmq.PUB)  # publish (broadcast)
socket.bind("tcp://*:5556")

rate = 50  # Hz


@contextlib.contextmanager
def controlled_time(t):
    tic = time.monotonic()
    yield
    toc = time.monotonic()
    remaining = t - (tic - toc)
    time.sleep(max(remaining, 0))


i = 0
while args.repeat == 0 or i < args.repeat:
    if i > 0:
        print(f"Re-serving: {i}")

    with open(args.input) as f:
        for line in f:
            with controlled_time(1 / rate):
                socket.send_string(line)

    i += 1
