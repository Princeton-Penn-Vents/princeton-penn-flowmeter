#!/usr/bin/env python3

import http.server
import json
from datetime import datetime

from processor.rotary import DICT
from patient.rotary_lcd import RotaryLCD
from processor.collector import Collector
from processor.rolling import get_last
from processor.handler import make_handler

# Initialize LCD
with RotaryLCD(DICT) as rotary:
    rotary.alarm_filter = lambda x: x in ["RR Max"]
    rotary.display()

    # Initialize Collector
    collector = Collector()
    collector.rotary = rotary

    server_address = ("0.0.0.0", 8100)
    with http.server.ThreadingHTTPServer(
        server_address, make_handler(collector)
    ) as httpd:
        httpd.serve_forever()
