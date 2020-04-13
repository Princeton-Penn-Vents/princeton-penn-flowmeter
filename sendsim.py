#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from itertools import chain
from sim.start_sims import start_sims
from processor.handler import make_handler
import argparse
import http.server
import numpy as np
import random
import sys
import time
from dataclasses import dataclass


@dataclass
class PseudoGenerator:
    parent: "OurServer"
    version_num: int
    last_ts: int = 0

    def prepare(self, *, from_timestamp=None):

        t_now = int(1000 * datetime.now().timestamp())
        if from_timestamp is None:
            values = 5000
        elif from_timestamp == 0:
            values == 30 * 50
        else:
            values = min(int(t_now - from_timestamp) // 50, 30 * 50)

        if self.parent.isDisconnected[self.version_num] > t_now:
            return {}

        sim = self.parent.sims[self.version_num]

        d = sim.get_from_timestamp(t_now, values)

        # enrich with stuff that comes from the analysis
        d["alarms"] = {}

        # enrich with stuff that comes from the overall patient server
        d["time"] = t_now

        return d


class OurServer:
    def serve_on_port(self, server_address, i):
        if server_address == 0:
            print("Starting disconnector service")
            self.update_disconnect()
        else:
            print(f"Serving on http://{server_address[0]}:{server_address[1]}")
            gen = PseudoGenerator(self, i)
            self.handler = make_handler(gen)
            self.httpd = http.server.ThreadingHTTPServer(server_address, self.handler)
            self.httpd.serve_forever()

    def __init__(self, args):
        self.done = False
        self.start_time = int(1000 * datetime.now().timestamp())  # milliseconds
        self.sims = start_sims(args.n, self.start_time, 12000000)  # milliseconds
        self.disconnect_prob = args.discon_prob
        self.isDisconnected = np.zeros(args.n)
        ip = args.bind

        if args.n > 1:
            print("Serving; press Control-C multiple times to quit")
            addresses = ((ip, args.port + i) for i in range(args.n))
            with ThreadPoolExecutor(max_workers=args.n + 1) as e:
                e.map(self.serve_on_port, chain(addresses, [0]), range(args.n + 1))
        else:
            port = args.port
            server_address = (ip, port)
            self.serve_on_port(server_address, 0)

    def update_disconnect(self):
        while True:
            rand = random.random()
            if rand < self.disconnect_prob:
                t_now = int(1000 * datetime.now().timestamp())
                sensor_num = random.randint(0, len(self.sims) - 1)
                self.isDisconnected[sensor_num] = t_now + 30 * 1000  # 30 seconds
                print("Disconnecting ", sensor_num, t_now)
            time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve values on network as JSON")
    parser.add_argument("--port", type=int, default=8100, help="First port to serve on")
    parser.add_argument(
        "--bind", default="0.0.0.0", help="Binding address (default: all)"
    )
    parser.add_argument("-n", type=int, default=1, help="How many ports to serve on")
    parser.add_argument(
        "--discon_prob",
        type=float,
        default=0.0,
        help="Probability of disconnecting a sim for 30 seconds each second",
    )
    args = parser.parse_args()
    print(args)
    myServer = OurServer(args)
