#!/usr/bin/env python3

from processor.config import ArgumentParser, init_logger

parser = ArgumentParser()
args = parser.parse_args()

init_logger()

import http.server
import sys
import threading
from functools import partial
import signal
from pathlib import Path

from nurse.qt import QtWidgets
from processor.settings import get_live_settings
from patient.rotary_gui import MainWindow, RotaryGUI
from processor.collector import Collector
from processor.handler import Handler

DIR = Path(__file__).parent.resolve()

with RotaryGUI(get_live_settings()) as rotary, Collector(rotary=rotary) as collector:

    rotary.live_load(DIR / "povm-live.yml")
    rotary.live_save(DIR / "povm-live.yml", every=10)

    server_address = ("0.0.0.0", 8100)
    with http.server.ThreadingHTTPServer(
        server_address, partial(Handler, collector)
    ) as httpd:

        thread = threading.Thread(target=httpd.serve_forever)
        thread.start()

        def shutdown_threaded_server():
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            print("Closing down server...")
            httpd.shutdown()
            thread.join()

        app = QtWidgets.QApplication([])
        main = MainWindow(rotary, collector, action=shutdown_threaded_server)

        def ctrl_c(_number, _frame):
            main.close()

        signal.signal(signal.SIGINT, ctrl_c)

        main.showNormal()
        sys.exit(app.exec_())
