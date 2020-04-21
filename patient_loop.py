#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="pofm.yml", help="YAML configuration file")
args = parser.parse_args()

import http.server
import yaml

from processor.settings import LIVE_DICT
from patient.rotary_lcd import RotaryLCD
from processor.collector import Collector
from processor.handler import serve

# Initialize LCD
with RotaryLCD(LIVE_DICT) as rotary:
    rotary.alarm_filter = lambda x: x in ["RR Max"]
    rotary.display()

    # Initialize Collector
    with open(args.config) as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
        collector = Collector(config=config)
    collector.rotary = rotary

    server_address = ("0.0.0.0", 8100)
    serve(server_address, collector)
