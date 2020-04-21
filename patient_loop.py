#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="pofm.yml", help="YAML configuration file")
args = parser.parse_args()

import signal
import yaml
from functools import partial
import http.server

from processor.settings import LIVE_DICT
from patient.rotary_lcd import RotaryLCD
from processor.collector import Collector
from processor.handler import Handler

# Read config file
with open(args.config) as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)

# Initialize LCD
with RotaryLCD(LIVE_DICT) as rotary, Collector(config=config) as collector:
    rotary.alarm_filter = lambda x: x in ["RR Max"]
    rotary.display()

    collector.rotary = rotary

    server_address = ("0.0.0.0", 8100)
    with http.server.ThreadingHTTPServer(
        server_address, partial(Handler, collector)
    ) as httpd:

        def ctrl_c(_number, _frame):
            print("Closing down server...")
            httpd.shutdown()

        signal.signal(signal.SIGINT, ctrl_c)

        httpd.serve_forever()
