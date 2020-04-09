#!/usr/bin/env python3

import sys
import numpy as np
import http.server
import argparse
import json
from datetime import datetime
from functools import partial
from start_sims import start_sims
from threading import Thread


def main(sim, timer):
    d = sim.get_batch(60)  # one minute until nursing gui collects data
    # enrich with stuff that comes from the analysis
    d["alarms"] = {}
    # enrich with stuff that comes from the overall patient server
    d["time"] = d["data"]["timestamps"][-1]
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
        self.handler = partial(Handler, self, i)
        self.httpd = http.server.ThreadingHTTPServer(server_address, self.handler)
        self.httpd.serve_forever()

    def __init__(self, args):
        self.done = False
        self.start_time = datetime.now().timestamp()
        self.sims = start_sims(args.n, self.start_time, 12000)
        ip = args.bind

        if args.n > 1:
            pool = []
            for i in range(args.n):
                port = args.port + i
                print(f"Serving on http://{ip}:{port}")
                server_address = (ip, port)
                pool.append(Thread(target=self.serve_on_port, args=[server_address, i]))

            for t in pool:
                t.start()

            for t in pool:
                t.join()

        else:
            port = args.port
            print(f"Serving on http://{ip}:{port}")
            server_address = (ip, port)
            self.serve_on_port(server_address, 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve values on network as JSON")
    parser.add_argument("--port", type=int, default=8100, help="First port to serve on")
    parser.add_argument("--bind", default="0.0.0.0", help="Binding address (default: all)")
    parser.add_argument("-n", type=int, default=1, help="How many ports to serve on")
    args = parser.parse_args()
    print(args)
    myServer = OurServer(args)
