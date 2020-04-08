#!/usr/bin/env python3

import sys
import numpy as np
import http.server
import argparse
import json
from sim import VentSim
from datetime import datetime
from functools import partial

def main(sim,timer):
    d = sim.get_batch(60) # one minute until nursing gui collects data
    #enrich with stuff that comes from the analysis
    d["alarms"] = {}
    #enrich with stuff that comes from the overall patient server
    d["time"]= d["data"]["timestamps"][-1]
    return json.dumps(d).encode("ascii")


# Ugly, better if the handler had options
# start_time = time.time()

class OurServer():
    def __init__(self,args):
        self.done = False
        self.start_time = datetime.now().timestamp()
        self.sim=VentSim(self.start_time,12000)

        class Handler(http.server.BaseHTTPRequestHandler):
            def __init__(self,parent,*args,**kwargs):
                self.parent=parent
                super().__init__(*args,**kwargs)
                
            def do_HEAD(self):
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

            def do_GET(self):
                #global start_time
                self.do_HEAD()
                self.wfile.write(main(self.parent.sim,self.parent.start_time))#time.time() - start_time))
        
        print(f"Serving on http://127.0.0.1:{args.port}")
        server_address = ("localhost", args.port)
        self.handler= partial(Handler, self)
        self.httpd = http.server.ThreadingHTTPServer(server_address, self.handler)
        self.httpd.serve_forever()

        


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve values on network as JSON")
    parser.add_argument("--port", type=int, default=8123, help="A port to serve on")
    args = parser.parse_args()
    myServer= OurServer(args)
