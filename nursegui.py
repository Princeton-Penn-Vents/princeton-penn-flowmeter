#!/usr/bin/env python3
from __future__ import annotations
import pyqtgraph as pg

# stdlib
import sys
import math
from string import Template
from pathlib import Path
import signal
import logging
from typing import Optional, List, Tuple
import threading
import itertools
from collections import Counter

from nurse.qt import (
    QtCore,
    QtWidgets,
    Qt,
    Slot,
    Signal,
    VBoxLayout,
    GridLayout,
)

from nurse.common import style_path, GraphInfo
from nurse.header import MainHeaderWidget
from nurse.grid import PatientSensor
from nurse.drilldown import DrilldownWidget
from nurse.connection_dialog import ConnectionDialog

from processor.generator import Generator
from processor.local_generator import LocalGenerator
from processor.remote_generator import RemoteGenerator
from processor.argparse import ArgumentParser
from processor.listener import FindBroadcasts
from processor.logging import make_nested_logger

DIR = Path(__file__).parent.resolve()

logger = logging.getLogger("povm")


class WaitingWidget(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addStretch()
        text = QtWidgets.QLabel("Waiting for a device to be connected...")
        text.setAlignment(Qt.AlignCenter)
        layout.addWidget(text)
        layout.addStretch()


class InjectDiscovery(QtCore.QObject):
    inject = Signal()


class MainStack(QtWidgets.QWidget):
    def __init__(
        self,
        parent,
        *,
        listener: FindBroadcasts,
        displays: Optional[int],
        sim: bool,
        addresses: List[str],
    ):
        super().__init__(parent)

        self.listener = listener

        layout = VBoxLayout(self)

        self.header = MainHeaderWidget(self)
        layout.addWidget(self.header)

        grid_layout = GridLayout()
        self.grid_layout = grid_layout
        layout.addLayout(grid_layout)

        self.graphs: List[PatientSensor] = []
        self.infos: List[WaitingWidget] = []

        if displays or addresses:
            disp_addr = itertools.zip_longest(
                range(displays or len(addresses)), addresses or []
            )
            for i, addr in disp_addr:
                local_logger = make_nested_logger(i)
                gen = (
                    RemoteGenerator(
                        address=addr or "tcp://127.0.0.1:8100", logger=local_logger
                    )
                    if not sim
                    else LocalGenerator(i=i + 1, logger=local_logger)
                )
                gen.run()  # Close must be called

                self.add_item(gen)
        else:
            waiting = WaitingWidget()
            self.infos.append(waiting)
            self.grid_layout.addWidget(waiting)

        self.qTimer = QtCore.QTimer()
        self.qTimer.timeout.connect(self.update_plots)
        self.qTimer.setSingleShot(True)
        self.qTimer.start()

        self.matching_dialog = MatchingDialog()
        self.matching_alert_timer = QtCore.QTimer()
        self.matching_alert_timer.timeout.connect(self.check_for_matching)
        self.matching_alert_timer.setInterval(1000)
        self.matching_alert_timer.start(1000)

        self.header.add_btn.clicked.connect(self.add_item_dialog)

        self.injector = InjectDiscovery()
        self.queue_lock = threading.Lock()

        if not displays and not addresses:
            self.injector.inject.connect(self.add_from_queue)
            self.listener.inject = lambda: self.injector.inject.emit()
            self.injector.inject.emit()

    @Slot()
    def add_from_queue(self):
        # The header doesn't display properly if this runs at the same time via
        # different triggers
        with self.queue_lock:
            while not self.listener.queue.empty():
                address = self.listener.queue.get()
                self.add_new_by_address(address.url)

    @Slot()
    def add_item_dialog(self):
        dialog = ConnectionDialog(
            self.listener, self.grid_layout.count() + 1, "tcp://127.0.0.1:8100"
        )
        if dialog.exec():
            self.add_new_by_address(dialog.connection_address())

    def add_new_by_address(self, addr: str):
        local_logger = make_nested_logger(len(self.graphs))
        gen = RemoteGenerator(address=addr, logger=local_logger)
        gen.run()
        self.add_item(gen)

    def _get_next_empty(self) -> Tuple[int, int]:
        ind = self.grid_layout.count()
        n_items = ind + 1
        height = math.ceil(math.sqrt(n_items))
        width = math.ceil(n_items / height)

        # Avoid wiggles when updating
        for i in range(width):
            self.grid_layout.setColumnStretch(i, 3)

        for i in range(height):
            for j in range(width):
                empty = self.grid_layout.itemAtPosition(i, j) is None
                if empty:
                    return i, j

        raise RuntimeError("No empty space!")

    def add_item(self, gen: Generator):
        ind = self.grid_layout.count()
        if len(self.graphs) == 0 and self.infos:
            waiting = self.infos.pop()
            self.grid_layout.removeWidget(waiting)
            waiting.setParent(None)
            ind = 0
        i, j = self._get_next_empty()

        drilldown: DrilldownWidget = self.parent().parent().drilldown
        drilldown.add_alarm_box()

        graph = PatientSensor(i=ind, gen=gen)
        self.graphs.append(graph)

        self.grid_layout.addWidget(graph, i, j)
        graph.set_plot()

    @Slot()
    def update_plots(self) -> None:
        if self.isVisible():
            for graph in self.graphs:
                graph.update_plot()
            self.qTimer.start(50)
        else:
            self.qTimer.start(500)

    @Slot()
    def check_for_matching(self) -> None:
        ids = Counter(graph.gen.sensor_id for graph in self.graphs)
        too_many = {k: v for k, v in ids.items() if v > 1 and k != 0}
        if too_many:
            self.matching_dialog.setText(
                "/n".join(
                    f"Too many ({v}) sensors with ID: {k}" for k, v in too_many.items()
                )
            )
            if not self.matching_dialog.isVisible():
                self.matching_dialog.open()
                self.matching_dialog.setWindowFlags(
                    self.matching_dialog.windowFlags()
                    | Qt.CustomizeWindowHint
                    | Qt.WindowTitleHint
                    | Qt.WindowStaysOnTopHint
                )
        else:
            if self.matching_dialog.isVisible():
                self.matching_dialog.close()


class MatchingDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.msg = QtWidgets.QLabel()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.msg)

    def setText(self, *args, **kwargs):
        self.msg.setText(*args, **kwargs)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *, displays: Optional[int], listener: FindBroadcasts, **kwargs):
        super().__init__()
        self.setObjectName("MainWindow")

        pg.setConfigOption("background", (0, 0, 0, 0))

        gis = GraphInfo()

        with open(style_path) as f:
            s = Template(f.read())
            t = s.substitute(**gis.graph_pens)
            self.setStyleSheet(t)

        stacked_widget = QtWidgets.QStackedWidget(self)
        self.setCentralWidget(stacked_widget)

        self.drilldown = DrilldownWidget(stacked_widget)
        self.main_stack = MainStack(
            stacked_widget, listener=listener, displays=displays, **kwargs
        )

        stacked_widget.addWidget(self.main_stack)
        stacked_widget.addWidget(self.drilldown)

        self.main_stack.header.fs_exit.clicked.connect(self.close)
        self.drilldown.return_btn.clicked.connect(self.drilldown_deactivate)

    @Slot()
    def drilldown_deactivate(self):
        self.drilldown.deactivate()
        stacked_widget = self.centralWidget()
        stacked_widget.setCurrentIndex(0)

    def drilldown_activate(self, i):
        self.drilldown.activate(i)
        stacked_widget = self.centralWidget()
        stacked_widget.setCurrentIndex(1)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            stacked_widget = self.centralWidget()
            if stacked_widget.currentIndex() != 0:
                self.drilldown_deactivate()

    def changeEvent(self, evt):
        super().changeEvent(evt)
        if evt.type() == QtCore.QEvent.WindowStateChange:
            self.main_stack.header.fs_exit.setVisible(
                self.windowState() & Qt.WindowFullScreen
            )

    def closeEvent(self, evt):
        for graph in self.main_stack.graphs:
            graph.gen.close()
        super().closeEvent(evt)


def main(argv, *, window: bool, debug: bool, **kwargs):

    if "Fusion" in QtWidgets.QStyleFactory.keys():
        QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    else:
        print("Fusion style is not available, display may be platform dependent")

    logger.info("Starting nursegui")

    app = QtWidgets.QApplication(argv)

    with FindBroadcasts() as listener:
        main = MainWindow(listener=listener, **kwargs)
        if not window:
            main.showFullScreen()
        else:
            size = app.screens()[0].availableSize()
            if size.width() < 2000 or size.height() < 1200:
                main.resize(int(size.width() * 0.95), int(size.height() * 0.85))
                main.showMaximized()
            else:
                main.resize(1920, 1080)
                main.showNormal()

        def ctrl_c(_sig_num, _stack_frame):
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            main.close()

        signal.signal(signal.SIGINT, ctrl_c)
        sys.exit(app.exec())


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Princeton Open Vent Monitor, nurse station graphical interface.",
        allow_abbrev=False,
        log_dir="nurse_log",
        log_stem="nursegui",
    )
    parser.add_argument("addresses", nargs="*", help="IP addresses to include")
    parser.add_argument(
        "--sim",
        action="store_true",
        help="Read from fake sim instead of remote generators (cannot be passed with addresses)",
    )

    parser.add_argument(
        "--window", action="store_true", help="Open in window instead of fullscreen"
    )
    parser.add_argument(
        "--displays", "-n", type=int, help="# of displays (Dynamic if not given)",
    )

    args, unparsed_args = parser.parse_known_args()

    if args.displays is not None and len(args.addresses) > args.displays:
        print(
            "Can't start with more addresses than displays. "
            "Increase one or decrease the other."
        )
        sys.exit(1)

    addresses = [
        f"tcp://{addr}" + ("" if ":" in addr else ":8100") for addr in args.addresses
    ]

    if args.addresses and args.sim:
        print("Cannot give addresses and sim together")
        sys.exit(1)

    main(
        argv=sys.argv[:1] + unparsed_args,
        addresses=addresses,
        sim=args.sim,
        displays=args.displays,
        window=args.window,
        debug=args.debug,
    )
