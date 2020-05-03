#!/usr/bin/env python3

from processor.config import ArgumentParser, init_logger

parser = ArgumentParser()
parser.add_argument("--port", "-p", type=int, default=8100, help="Select a port")
args = parser.parse_args()

init_logger()

import sys
import signal
from pathlib import Path

from nurse.qt import QtWidgets
from processor.settings import get_live_settings
from patient.rotary_gui import MainWindow, RotaryGUI
from processor.collector import Collector
from processor.broadcast import Broadcast

DIR = Path(__file__).parent.resolve()

with RotaryGUI(get_live_settings()) as rotary, Collector(
    rotary=rotary, port=args.port
) as collector, Broadcast("patientgui", port=args.port):

    rotary.live_load(DIR / "povm-live.yml")
    rotary.live_save(DIR / "povm-live.yml", every=10)

    app = QtWidgets.QApplication([])
    main = MainWindow(rotary, collector)

    def ctrl_c(_number, _frame):
        main.close()

    signal.signal(signal.SIGINT, ctrl_c)

    main.showNormal()
    sys.exit(app.exec_())
