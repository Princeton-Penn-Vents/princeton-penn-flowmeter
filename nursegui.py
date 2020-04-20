#!/usr/bin/env python3
import pyqtgraph as pg

# stdlib
import argparse
import numpy as np
import os
import sys
import math
from string import Template

from nurse.qt import (
    QtCore,
    QtWidgets,
    QtGui,
    Qt,
    Slot,
    HBoxLayout,
    VBoxLayout,
    FormLayout,
    GridLayout,
)

from nurse.common import style_path, GraphInfo
from nurse.header import MainHeaderWidget
from nurse.grid import PatientSensor
from nurse.drilldown import DrilldownWidget

from processor.generator import Status
from processor.local_generator import LocalGenerator
from processor.remote_generator import RemoteGenerator

logging_directory = None


class MainStack(QtWidgets.QWidget):
    def __init__(self, *, ip, port, displays, logging, offset):
        super().__init__()

        height = math.ceil(math.sqrt(displays))
        width = math.ceil(displays / height)

        layout = VBoxLayout(self)

        self.header = MainHeaderWidget(self)
        layout.addWidget(self.header)

        grid_layout = GridLayout()
        layout.addLayout(grid_layout)

        # Avoid wiggles when updating
        for i in range(width):
            grid_layout.setColumnStretch(i, 3)

        self.graphs = []

        for i in range(displays):
            # A bit hacky for testing - will become a --debug flag later
            if port is not None:
                if i == 7:  # hack to make this one always disconnected
                    gen = RemoteGenerator()
                else:
                    gen = RemoteGenerator(ip=ip, port=port + i)
            else:
                status = Status.OK if i % 7 != 1 else Status.ALERT
                if i == 7:
                    status = Status.DISCON
                gen = LocalGenerator(status, logging=logging)

            graph = PatientSensor(i + offset, gen=gen, logging=logging)
            self.graphs.append(graph)

            grid_layout.addWidget(graph, *reversed(divmod(i, height)))
            graph.set_plot()

            graph.qTimer = QtCore.QTimer()
            graph.qTimer.timeout.connect(graph.update_plot)
            graph.qTimer.setSingleShot(True)
            graph.qTimer.start()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *, ip, port, displays, **kwargs):
        super().__init__()
        self.setObjectName("MainWindow")

        # May be expensive, probably only enable if we multithread the draw
        # pg.setConfigOptions(antialias=True)
        pg.setConfigOption("background", (0, 0, 0, 0))

        gis = GraphInfo()

        with open(style_path) as f:
            s = Template(f.read())
            t = s.substitute(**gis.graph_pens)
            self.setStyleSheet(t)

        self.main_stack = MainStack(ip=ip, port=port, displays=displays, **kwargs)
        stacked_widget = QtWidgets.QStackedWidget()
        stacked_widget.addWidget(self.main_stack)

        self.drilldown = DrilldownWidget(parent=self)
        self.drilldown.return_btn.clicked.connect(self.drilldown_deactivate)
        stacked_widget.addWidget(self.drilldown)

        self.setCentralWidget(stacked_widget)

        self.main_stack.header.fs_exit.clicked.connect(self.close)

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


def main(argv, *, fullscreen, **kwargs):
    if "Fusion" in QtWidgets.QStyleFactory.keys():
        QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    else:
        print("Fusion style is not available, display may be platform dependent")

    app = QtWidgets.QApplication(argv)

    main = MainWindow(**kwargs)
    if fullscreen:
        main.showFullScreen()
    else:
        size = app.screens()[0].availableSize()
        if size.width() < 2000 or size.height() < 1200:
            main.resize(int(size.width() * 0.95), int(size.height() * 0.85))
            main.showMaximized()
        else:
            main.resize(1920, 1080)
            main.showNormal()

    sys.exit(app.exec_())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--ip", default="127.0.0.1", help="Select an ip address")
    parser.add_argument(
        "--port", type=int, help="Select a starting port (8100 recommended)"
    )
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument(
        "--displays",
        "-n",
        type=int,
        default=20,
        help="# of displays, currently not dynamic",
    )
    parser.add_argument(
        "--offset", type=int, default=0, help="Offset the numbers by this amount"
    )
    parser.add_argument(
        "--logging",
        help="If a directory name, local generators fill *.dat files in that directory with time-series (time, flow, pressure)",
    )

    args, unparsed_args = parser.parse_known_args()

    main(argv=sys.argv[:1] + unparsed_args, **(args.__dict__))
