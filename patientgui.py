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
from processor.settings import LIVE_DICT
from patient.rotary_gui import MainWindow, RotaryGUI
from processor.collector import Collector
from processor.handler import serve

# Initialize LCD replacement
with RotaryGUI(LIVE_DICT) as rotary:

    # Initialize Collector
    with open(args.config) as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
        collector = Collector(config=config)
    collector.rotary = rotary

    server_address = ("0.0.0.0", 8100)

    thread = threading.Thread(target=serve, args=(server_address, collector))
    thread.start()

    app = QtWidgets.QApplication([])
    main = MainWindow(rotary, collector)
    main.showNormal()
    sys.exit(app.exec_())
