#!/usr/bin/env python3

import http.server
import json
from datetime import datetime
import atexit

from processor.rotary import DICT
from patient.rotary_lcd import RotaryLCD
from processor.collector import Collector
from processor.rolling import get_last

# Initialize LCD
rotary = RotaryLCD(DICT)
rotary.display()

atexit.register(rotary.close)

# Initialize Collector
collector = Collector()
collector.set_rotary(rotary)

passing_window = 100 * 5

# Captures collector
def prepare():
    collector.get_data()
    # collector.analyze()

    return {
        "version": 1,
        "time": datetime.now().timestamp(),
        "alarms": {},
        "data": {
            "timestamps": get_last(collector.timestamps, passing_window).tolist(),
            "flows": get_last(collector.flow/480, passing_window).tolist(),
            "pressures": get_last((collector.pressure-255)/12+7.5, passing_window).tolist(),
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
        self.wfile.write(json.dumps(prepare()).encode("ascii"))


server_address = ("0.0.0.0", 8100)
httpd = http.server.ThreadingHTTPServer(server_address, Handler)
httpd.serve_forever()
