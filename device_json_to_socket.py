#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input single-line json file")
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


with open(args.input) as f:
    for line in f:
        with controlled_time(1 / rate):
            socket.send_string(line)
