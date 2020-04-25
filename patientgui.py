#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="pofm.yml", help="YAML configuration file")
args = parser.parse_args()

import http.server
import sys
import threading
from functools import partial
import signal

from nurse.qt import QtWidgets
from processor.settings import get_live_settings
from patient.rotary_gui import MainWindow, RotaryGUI
from processor.collector import Collector
from processor.handler import Handler


with RotaryGUI(get_live_settings()) as rotary, Collector(rotary=rotary) as collector:

    server_address = ("0.0.0.0", 8100)
    with http.server.ThreadingHTTPServer(
        server_address, partial(Handler, collector)
    ) as httpd:

        thread = threading.Thread(target=httpd.serve_forever)
        thread.start()

        def shutdown_threaded_server():
            print("Closing down server...")
            httpd.shutdown()
            thread.join()

        app = QtWidgets.QApplication([])
        main = MainWindow(rotary, collector, action=shutdown_threaded_server)

        def ctrl_c(_number, _frame):
            shutdown_threaded_server()
            main.close()

        signal.signal(signal.SIGINT, ctrl_c)

        main.showNormal()
        sys.exit(app.exec_())
