#!/usr/bin/env python3

from processor.config import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-n", default=2.0, type=float, help="Timeout between reporting")
parser.add_argument("--ip", default="127.0.0.1", help="Select an ip address")
parser.add_argument(
    "--port", type=int, help="Select a starting port (8100 recommended)"
)

arg = parser.parse_args()

import time
import numpy as np

from processor.local_generator import LocalGenerator
from processor.remote_generator import RemoteGenerator
from processor.generator import Generator

gen: Generator

if arg.port is not None:
    print(f"Remote: tcp://{arg.ip}:{arg.port}")
    gen = RemoteGenerator(ip=arg.ip, port=arg.port)
else:
    print("Local Generator")
    gen = LocalGenerator()

print(f"Reporting every {arg.n} seconds, use Ctrl-C to exit.")

with gen:
    while True:
        time.sleep(arg.n)

        with np.printoptions(threshold=6, precision=4, floatmode="fixed", linewidth=95):
            print(f"--- Current status ---")
            print(f"gen.timestamps:    {gen.timestamps} ({len(gen.timestamps)} length)")
            print(f"gen.flow:          {gen.flow} ({len(gen.flow)} length)")
            print(f"gen.pressure:      {gen.pressure} ({len(gen.pressure)} length)")
            print(f"gen.volume (calc): {gen.volume} ({len(gen.volume)} length)")
            print()
