#!/usr/bin/env python3

import sys
import numpy as np
import http.server
import argparse
import json
from datetime import datetime
from functools import partial
from sim.start_sims import start_sims
from concurrent.futures import ThreadPoolExecutor


def main(sim, timer):
    t_now = int(1000 * datetime.now().timestamp())
    d = sim.get_from_timestamp(t_now, 5000)
    # enrich with stuff that comes from the analysis
    d["alarms"] = {}
    # enrich with stuff that comes from the overall patient server
    d["time"] = t_now
    return json.dumps(d).encode("ascii")


# Ugly, better if the handler had options
# start_time = time.time()
class Handler(http.server.BaseHTTPRequestHandler):
    def __init__(self, parent, version_num, *args, **kwargs):
        self.parent = parent
        self.version_num = version_num
        super().__init__(*args, **kwargs)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        self.do_HEAD()
        self.wfile.write(
            main(self.parent.sims[self.version_num], self.parent.start_time)
        )  # time.time() - start_time))


class OurServer:
    def serve_on_port(self, server_address, i):
        print(f"Serving on http://{server_address[0]}:{server_address[1]}")
        self.handler = partial(Handler, self, i)
        self.httpd = http.server.ThreadingHTTPServer(server_address, self.handler)
        self.httpd.serve_forever()

    def __init__(self, args):
        self.done = False
        self.start_time = int(1000 * datetime.now().timestamp())  # milliseconds
        self.sims = start_sims(args.n, self.start_time, 12000000)  # milliseconds
        ip = args.bind

        if args.n > 1:
            print("Serving; press Control-C multiple times to quit")
            addresses = ((ip, args.port + i) for i in range(args.n))
            with ThreadPoolExecutor(max_workers=args.n) as e:
                e.map(self.serve_on_port, addresses, range(args.n))

        else:
            port = args.port
            server_address = (ip, port)
            self.serve_on_port(server_address, 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve values on network as JSON")
    parser.add_argument("--port", type=int, default=8100, help="First port to serve on")
    parser.add_argument(
        "--bind", default="0.0.0.0", help="Binding address (default: all)"
    )
    parser.add_argument("-n", type=int, default=1, help="How many ports to serve on")
    args = parser.parse_args()
    print(args)
    myServer = OurServer(args)
