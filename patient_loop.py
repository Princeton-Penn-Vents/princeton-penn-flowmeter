#!/usr/bin/env python3

from processor.config import ArgumentParser

parser = ArgumentParser()
args = parser.parse_args()

import signal
from functools import partial
import http.server
import threading

from processor.settings import get_live_settings
from patient.rotary_lcd import RotaryLCD
from processor.collector import Collector
from processor.handler import Handler

# Initialize LCD
with RotaryLCD(get_live_settings()) as rotary, Collector() as collector:
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
