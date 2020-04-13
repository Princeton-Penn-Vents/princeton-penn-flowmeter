#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from itertools import chain
from sim.start_sims import start_sims
import argparse
import http.server
import json
import numpy as np
import random
import sys
import time
from urllib.parse import urlparse, parse_qs


def main(sim, t_now):
    d = sim.get_from_timestamp(t_now, 5000)
    # enrich with stuff that comes from the analysis
    d["alarms"] = {}
    # enrich with stuff that comes from the overall patient server
    d["time"] = t_now
    return json.dumps(d).encode("ascii")


class Handler(http.server.BaseHTTPRequestHandler):
    def __init__(self, parent, version_num, *args, **kwargs):
        self.parent = parent
        self.version_num = version_num
        super().__init__(*args, **kwargs)

    def parse_url(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return parse_qs(parsed.query)

    def do_HEAD(self):
        if self.parse_url() is None:
            self.send_response(404)
            return
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        return True

    def do_GET(self):
        parsed_path = urlparse(self.path)
        print(parsed_path.path)
        print(parsed_path.query)
        print(self.parse_url())

        t_now = int(1000 * datetime.now().timestamp())

        if self.parent.isDisconnected[self.version_num] <= t_now:
            if self.do_HEAD():
                self.wfile.write(main(self.parent.sims[self.version_num], t_now))
        else:
            self.send_error(408)


class OurServer:
    def serve_on_port(self, server_address, i):
        if server_address == 0:
            print("Starting disconnector service")
            self.update_disconnect()
        else:
            print(f"Serving on http://{server_address[0]}:{server_address[1]}")
            self.handler = partial(Handler, self, i)
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
