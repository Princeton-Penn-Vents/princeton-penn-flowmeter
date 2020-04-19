#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="pofm.yml", help="YAML configuration file")
args = parser.parse_args()

import http.server
import yaml
import sys
import threading

from nurse.qt import QtCore, QtWidgets, QtGui, Slot, Qt
from processor.rotary import DICT
from patient.rotary_gui import MainWindow
from processor.collector import Collector
from processor.rotary import LocalRotary
from processor.handler import make_handler

# Initialize LCD replacement
with LocalRotary(DICT) as rotary:
    rotary.alarm_filter = lambda x: x in ["RR Max"]

    # Initialize Collector
    with open(args.config) as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
        collector = Collector(config=config)
    collector.rotary = rotary

    server_address = ("0.0.0.0", 8100)
    with http.server.ThreadingHTTPServer(
        server_address, make_handler(collector)
    ) as httpd:
        thread = threading.Thread(target=httpd.serve_forever)
        thread.start()

        app = QtWidgets.QApplication([])
        main = MainWindow(rotary, collector)
        main.showNormal()
        sys.exit(app.exec_())
