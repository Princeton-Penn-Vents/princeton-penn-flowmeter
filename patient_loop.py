#!/usr/bin/env python3

from processor.config import ArgumentParser, init_logger

parser = ArgumentParser()
args = parser.parse_args()

init_logger()

import signal
from functools import partial
import http.server
import threading
from pathlib import Path

from processor.settings import get_live_settings
from patient.rotary_lcd import RotaryLCD
from processor.collector import Collector
from processor.handler import Handler

DIR = Path(__file__).parent.resolve()

# Initialize LCD
with RotaryLCD(get_live_settings()) as rotary, Collector(rotary=rotary) as collector:
    rotary.live_load(DIR / "pofm-live.yml")
    rotary.live_save(DIR / "pofm-live.yml", every=10)

    server_address = ("0.0.0.0", 8100)
    with http.server.ThreadingHTTPServer(
        server_address, partial(Handler, collector)
    ) as httpd:

        thread = threading.Thread(target=httpd.serve_forever)
        thread.start()

        def ctrl_c(_number, _frame):
            print("Closing down server...")
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            httpd.shutdown()

        signal.signal(signal.SIGINT, ctrl_c)

        thread.join()
