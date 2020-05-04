#!/usr/bin/env python3

from processor.argparse import ArgumentParser

parser = ArgumentParser(type="patient")
parser.add_argument("--port", "-p", type=int, default=8100, help="Select a port")
args = parser.parse_args()


import signal
import threading
from pathlib import Path

from processor.settings import get_live_settings
from patient.rotary_lcd import RotaryLCD
from processor.collector import Collector
from processor.broadcast import Broadcast

DIR = Path(__file__).parent.resolve()

# Initialize LCD
with RotaryLCD(get_live_settings()) as rotary, Collector(
    rotary=rotary, port=args.port
) as collector, Broadcast("patient_loop", port=args.port, live=4):
    rotary.live_load(DIR / "povm-live.yml")
    rotary.live_save(DIR / "povm-live.yml", every=10)

    forever = threading.Event()

    def close(_number, _frame):
        print("Closing down server...")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        forever.set()

    signal.signal(signal.SIGINT, close)
    signal.signal(signal.SIGTERM, close)

    forever.wait()
