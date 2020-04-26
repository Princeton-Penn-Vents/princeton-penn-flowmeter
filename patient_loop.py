#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="pofm.yml", help="YAML configuration file")
args = parser.parse_args()

import signal
import yaml
from functools import partial
import http.server
import threading

from processor.settings import get_live_settings
from patient.rotary_lcd import RotaryLCD
from processor.collector import Collector
from processor.handler import Handler
from processor.config import config

if args.config:
    config.set_file(args.config)

# Initialize LCD
with RotaryLCD(get_live_settings()) as rotary, Collector() as collector:
    rotary.alarm_filter = lambda x: x in ["RR Max"]
    rotary.display()

    collector.rotary = rotary

    server_address = ("0.0.0.0", 8100)
    with http.server.ThreadingHTTPServer(
        server_address, partial(Handler, collector)
    ) as httpd:

        thread = threading.Thread(target=httpd.serve_forever)
        thread.start()

        def ctrl_c(_number, _frame):
            print("Closing down server...")
            httpd.shutdown()

        signal.signal(signal.SIGINT, ctrl_c)

        thread.join()
