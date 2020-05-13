#!/usr/bin/env python3

from processor.argparse import ArgumentParser

parser = ArgumentParser(log_dir="patient_log", log_stem="patient_loop")
parser.add_argument("--port", "-p", type=int, default=8100, help="Select a port")
args = parser.parse_args()


import signal
import threading
from contextlib import ExitStack


from processor.settings import get_live_settings
from patient.rotary_lcd import RotaryLCD
from processor.collector import Collector
from processor.broadcast import Broadcast
from patient.mac_address import get_box_name
from processor.config import get_data_dir


# Initialize LCD
with ExitStack() as stack:
    rotary = stack.enter_context(RotaryLCD(get_live_settings()))

    forever = threading.Event()

    def close(_number, _frame):
        print("Closing down server...")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        forever.set()

    rotary.backlight.magenta()
    rotary.lcd.upper("POVM Box name:")
    rotary.lcd.lower("Getting name...")
    rotary.lcd.lower(f"{get_box_name():<20}")
    forever.wait(3)

    rotary.backlight.green(light=True)
    rotary.lcd.upper("Turn to select alarm ")
    rotary.lcd.lower("Push and turn to set ")
    forever.wait(2)

    rotary.backlight.white()

    collector = stack.enter_context(Collector(rotary=rotary, port=args.port))
    stack.enter_context(Broadcast("patient_loop", port=args.port, live=5))

    rotary.live_load(get_data_dir() / "povm-live.yml")
    rotary.live_save(get_data_dir() / "povm-live.yml", every=10)

    signal.signal(signal.SIGINT, close)
    signal.signal(signal.SIGTERM, close)

    forever.wait()
