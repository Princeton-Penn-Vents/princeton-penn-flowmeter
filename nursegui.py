#!/usr/bin/env python3

import signal

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSlot as Slot  # Named like PySide
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap, QFont

import pyqtgraph as pg

# stdlib
import argparse
import numpy as np
import os
import sys
from pathlib import Path

from nurse.generator import Status
from nurse.local_generator import LocalGenerator
from nurse.remote_generator import RemoteGenerator

DIR = Path(__file__).parent.absolute()


class AlertWidget(QtWidgets.QWidget):
    @property
    def status(self):
        return Status[self.property("status")]

    @status.setter
    def status(self, value):
        self.setProperty("status", value.name)
        self.name_btn.style().unpolish(self.name_btn)
        self.name_btn.style().polish(self.name_btn)
        # the rest is in the style.css

    def __init__(self, i: int):
        super().__init__()
        column_layout = QtWidgets.QVBoxLayout()
        self.setLayout(column_layout)

        self.name_btn = QtWidgets.QPushButton("\n".join(str(i + 1)))
        column_layout.addWidget(self.name_btn)  # , 2)


class GraphicsView(pg.GraphicsView):
    def __init__(self, *args, i, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_plot = i

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            print(f"Clicked {self.current_plot + 1}")
        super().mousePressEvent(event)


class PatientSensor(QtGui.QFrame):
    @property
    def status(self):
        return Status[self.property("status")]

    @status.setter
    def status(self, value):
        self.setProperty("status", value.name)
        self.style().unpolish(self)
        self.style().polish(self)

    def __init__(self, i, *args, ip, port, **kwargs):
        super().__init__(*args, **kwargs)
        #       frame = QtGui.QFrame()
        #       frame.setSpacing(0)
        #       frame.setContentsMargins(0, 0, 0, 0)
        #       self.setLayout(frame)

        outer_layout = QtWidgets.QVBoxLayout()
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(outer_layout)

        upper = QtWidgets.QWidget()
        outer_layout.addWidget(upper)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        upper.setLayout(layout)
        # upper.setStyleSheet("background-color: #FEFFCF;");

        graphview = GraphicsView(parent=self, i=i)
        graphlayout = pg.GraphicsLayout()
        graphlayout.setContentsMargins(0, 0, 0, 0)
        graphview.setCentralWidget(graphlayout)
        layout.addWidget(graphview)  # , 7)

        self.graph_flow = graphlayout.addPlot(x=[], y=[], name="Flow")
        #        self.graph_flow.setLabel("left", "F", units="L/m")
        self.graph_flow.setMouseEnabled(False, False)
        self.graph_flow.invertX()

        graphlayout.nextRow()

        self.graph_pressure = graphlayout.addPlot(x=[], y=[], name="Pressure")
        #        self.graph_pressure.setLabel("left", "P", units="cm H2O")
        self.graph_pressure.setMouseEnabled(False, False)
        self.graph_pressure.invertX()

        graphlayout.nextRow()

        self.graph_volume = graphlayout.addPlot(x=[], y=[], name="Volume")
        #        self.graph_volume.setLabel("left", "V", units="mL")
        self.graph_volume.setMouseEnabled(False, False)
        self.graph_volume.invertX()

        self.alert = AlertWidget(i)

        layout.addWidget(self.alert)  # , 3)

        lower = QtWidgets.QWidget()
        # lower.setStyleSheet("background-color: #FEFFCF;");
        outer_layout.addWidget(lower)
        lower_layout = QtWidgets.QGridLayout()
        lower.setLayout(lower_layout)

        self.info_strings = [
            "RR",  # (L/m)
            "TVe",  # (mL)
            "TVi",  # (mL/m)
            "PIP",  # (cm H2O)
        ]

        # dummy
        self.info_vals = [12.2, 20.0, 12.2, 20.0]

        nCols = len(self.info_strings)
        self.info_widgets = []
        self.val_widgets = []
        self.widget_lookup = {}
        for j in range(len(self.info_strings)):
            self.info_widgets.append(QtWidgets.QLabel(self.info_strings[j]))
            self.val_widgets.append(QtWidgets.QLabel(str(int(self.info_vals[j]))))
            self.info_widgets[-1].setContentsMargins(0, 0, 0, 0)
            self.val_widgets[-1].setContentsMargins(0, 0, 0, 0)
            lower_layout.addWidget(self.info_widgets[-1], j // nCols, 2 * (j % nCols))
            lower_layout.addWidget(
                self.val_widgets[-1], j // nCols, 1 + 2 * (j % nCols)
            )
            self.widget_lookup[self.info_strings[j]] = j

        status = Status.OK if i % 7 != 1 else Status.ALERT

        if port is not None:
            self.flow = RemoteGenerator(ip=ip, port=port + i)
        else:
            self.flow = LocalGenerator(status)

        self.alert.status = self.flow.status
        self.status = self.flow.status
        self.alert.name_btn.clicked.connect(self.click_number)

    @Slot()
    def click_number(self):
        number, ok = QtWidgets.QInputDialog.getText(self, "Select port", "Pick a port")
        if ok:
            try:
                port = int(number)
            except ValueError:
                self.flow = LocalGenerator(Status.DISCON)
                return
            self.flow = RemoteGenerator(port=port)

    def set_plot(self):
        self.flow.get_data()
        self.flow.analyze()

        pen = pg.mkPen(color=(120, 255, 50), width=2)
        self.curve_flow = self.graph_flow.plot(self.flow.time, self.flow.flow, pen=pen)
        pen = pg.mkPen(color=(255, 120, 50), width=2)
        self.curve_pressure = self.graph_pressure.plot(
            self.flow.time, self.flow.pressure, pen=pen
        )
        pen = pg.mkPen(color=(50, 120, 255), width=2)
        self.curve_volume = self.graph_volume.plot(
            self.flow.time, self.flow.volume, pen=pen
        )
        # the y limits ought to be configurable.
        yLims = {}
        yLims["flow"] = (-30, 30)
        yLims["pressure"] = (0, 20)
        yLims["volume"] = (-1000, 1000)

        yTicks = {}
        yTicks["flow"] = [-25, 0, 25]
        yTicks["pressure"] = [0, 15]
        yTicks["volume"] = [-1000, 1000]

        self.graph_flow.setRange(xRange=(30, 0), yRange=yLims["flow"])
        self.graph_pressure.setRange(xRange=(30, 0), yRange=yLims["pressure"])
        self.graph_volume.setRange(xRange=(30, 0), yRange=yLims["volume"])
        dy = [(value, str(value)) for value in yTicks["flow"]]
        self.graph_flow.getAxis("left").setTicks([dy, []])
        dy = [(value, str(value)) for value in yTicks["pressure"]]
        self.graph_pressure.getAxis("left").setTicks([dy, []])
        dy = [(value, str(value)) for value in yTicks["volume"]]
        self.graph_volume.getAxis("left").setTicks([dy, []])

        self.graph_flow.setXLink(self.graph_pressure)
        self.graph_flow.setXLink(self.graph_volume)
        self.graph_flow.hideAxis("bottom")
        self.graph_pressure.hideAxis("bottom")

        pen = pg.mkPen(color=(220, 220, 50), width=3)

        # self.upper = self.graph_flow.addLine(y=8, pen=pen)
        # self.lower = self.graph_flow.addLine(y=-2, pen=pen)

    @Slot()
    def update_plot(self):
        self.flow.get_data()
        self.flow.analyze()

        self.curve_flow.setData(self.flow.time, self.flow.flow)
        self.curve_pressure.setData(self.flow.time, self.flow.pressure)
        self.curve_volume.setData(self.flow.time, self.flow.volume)

        self.alert.status = self.flow.status
        self.status = self.flow.status

        for key in self.widget_lookup:
            val = self.widget_lookup[key]
            v = np.random.uniform(5.0, 15.0)
            self.val_widgets[val].setText(str(int(v)))


class PatientGrid(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Avoid wiggles when updating
        for i in range(5):
            layout.setColumnStretch(i, 3)

        self.setLayout(layout)


class MainStack(QtWidgets.QWidget):
    def __init__(self, *args, ip, port, refresh, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        headerwidget = HeaderWidget(self)
        layout.addWidget(headerwidget)
        patientwidget = PatientGrid(self)
        layout.addWidget(patientwidget)

        self.setLayout(layout)

        self.graphs = [
            PatientSensor(i, ip=ip, port=port, parent=patientwidget) for i in range(20)
        ]
        for i, graph in enumerate(self.graphs):
            patientwidget.layout().addWidget(self.graphs[i], *reversed(divmod(i, 4)))
            graph.set_plot()

            graph.qTimer = QtCore.QTimer()
            graph.qTimer.setInterval(refresh)
            graph.qTimer.timeout.connect(graph.update_plot)
            graph.qTimer.start()

    def closeEvent(self):
        for graph in self.graphs:
            graph.flow.close()


class HeaderWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(0)
        layout.setColumnStretch(1,1)
        layout.setColumnStretch(2,1)
        layout.setColumnStretch(3,0)
        layout.setContentsMargins(0, 0, 0, 0)
        logo1 = QPixmap("images/PUsig2-158C-shield.png").scaledToWidth(18)
        logo2 = QPixmap("images/nsf-logo-100.png").scaledToWidth(25)
        logo1label = QtWidgets.QLabel()
        logo1label.setPixmap(logo1)
        logo2label = QtWidgets.QLabel()
        logo2label.setPixmap(logo2)
        text1 = QtWidgets.QLabel(
            "  Princeton Open Vent Monitor"
        )
        text1.setFont(QtGui.QFont("Times", 20, QtGui.QFont.Bold))
        text1.setStyleSheet("color: #F58025;");
        text2 = QtWidgets.QLabel(
            "Lets put our color legend and units here together with other drill down options"
        )
        text2.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo1label)
        layout.addWidget(text1)
        layout.addWidget(text2)
        layout.addWidget(logo2label)
        self.setLayout(layout)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, ip, port, refresh, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("MainWindow")
        self.resize(1920, 1080)

        # May be expensive, probably only enable if we multithread the draw
        # pg.setConfigOptions(antialias=True)
        pg.setConfigOption("background", (0, 0, 0, 0))

        # Replace with proper importlib.resources if made a package
        with open(DIR / "nurse" / "style.css") as f:
            self.setStyleSheet(f.read())

        centralwidget = MainStack(
            self, *args, ip=ip, port=port, refresh=refresh, **kwargs
        )
        self.setCentralWidget(centralwidget)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.centralWidget().closeEvent()
        super().closeEvent(event)


def _interrupt_handler(signum, frame):
    QtGui.QApplication.quit()


def main(argv, *, fullscreen, no_display, **kwargs):
    app = QtWidgets.QApplication(argv)
    main = MainWindow(**kwargs)
    if no_display:
        # if there's no display, KeyboardInterrupt is the only way to quit
        signal.signal(signal.SIGINT, _interrupt_handler)
    else:
        if fullscreen:
            main.showFullScreen()
        else:
            main.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="Select an ip address")
    parser.add_argument(
        "--refresh", default=1000, type=int, help="Screen refresh timer, in ms"
    )
    parser.add_argument(
        "--port", type=int, help="Select a starting port (8100 recommended)"
    )
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--no-display", action="store_true")

    arg, unparsed_args = parser.parse_known_args()
    main(
        argv=sys.argv[:1] + unparsed_args,
        ip=arg.ip,
        port=arg.port,
        fullscreen=arg.fullscreen,
        no_display=arg.no_display,
        refresh=arg.refresh,
    )
