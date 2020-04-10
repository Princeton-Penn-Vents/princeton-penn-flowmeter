#!/usr/bin/env python3

import http.server
import json
from datetime import datetime

from patient.rotarty_lcd import RotaryLCD
from patient.collector import Collector
from sim.rolling import get_last

# Initialize LCD
rotary = RotaryLCD()
rotary.display()

# Initialize Collector
collector = Collector()

passing_window = 100 * 5

# Captures collector
def prepare():
    collector.get_data()

    return {
        "version": 1,
        "time": datetime.now().timestamp(),
        "alarms": {},
        "data": {
            "timestamps": get_last(collector.time, passing_window),
            "flows": get_last(collector.flows, passing_window),
            "pressures": get_last(collector.pressure, passing_window),
        },
    }


class Handler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        self.do_HEAD()
        self.wfile.write(json.dumps(prepare()))


httpd = http.server.threadinghttpserver(server_address, Handler)
httpd.serve_forever()
