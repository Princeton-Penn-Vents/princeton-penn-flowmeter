#!/usr/bin/env python3

import http.server
import json
from datetime import datetime
import atexit

from processor.rotary import DICT
from patient.rotary_lcd import RotaryLCD
from processor.collector import Collector
from processor.rolling import get_last
from processor.handler import make_handler

# Initialize LCD
rotary = RotaryLCD(DICT)
rotary.alarm_filter = lambda x: x in ["RR Max"]
rotary.display()

atexit.register(rotary.close)

# Initialize Collector
collector = Collector()
collector.rotary = rotary

server_address = ("0.0.0.0", 8100)
with http.server.ThreadingHTTPServer(server_address, make_handler(collector)) as httpd:
    httpd.serve_forever()
