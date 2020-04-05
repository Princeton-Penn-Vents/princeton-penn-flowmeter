#!/usr/bin/env python3

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QTimer
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import numpy as np
import sys
import os
import enum


class Status(enum.Enum):
    OK = enum.auto()
    ALERT = enum.auto()
    DISCON = enum.auto()


class AlertWidget(QtWidgets.QWidget):
    @QtCore.pyqtProperty(str)
    def status(self):
        return self._status

    @status.setter
    def status(self, value: str):
        self.alert.setText(value)
        self._status = value

    def __init__(self, i: int):
        super().__init__()
        self._status = Status.DISCON.name
        column_layout = QtWidgets.QVBoxLayout()
        self.setLayout(column_layout)

        name = QtWidgets.QLabel(str(i + 1))
        # name.setStyleSheet("font-size: 30px;");
        name.setAlignment(QtCore.Qt.AlignCenter)
        column_layout.addWidget(name)

        self.alert = QtWidgets.QLabel("OK")
        self.alert.setAlignment(QtCore.Qt.AlignCenter)
        column_layout.addWidget(self.alert)


class PatientSensor(QtWidgets.QWidget):
    def __init__(self, i):
        super().__init__()
        self._alert_status = Status.DISCON.name

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

        self.graph = pg.PlotWidget()
        self.graph.setLabel("left", "Flow", units="L/m")
        self.graph.setLabel("bottom", "Time", units="seconds")
        layout.addWidget(self.graph)

        self.alert = AlertWidget(i)
        layout.addWidget(self.alert)

        lower = QtWidgets.QWidget()
        outer_layout.addWidget(lower)
        lower_layout = QtWidgets.QGridLayout()
        lower.setLayout(lower_layout)

        self.info_strings = [
            "MinFlow (L/m):",
            "MaxFlow (L/m):",
            "AveMinFlow (L/m):",
            "TimeWindow (s):",
            "AveFlow (L/m):",
            "CurrentFlow (L/m):",
        ]

        # dummy
        self.info_vals = [12.2, 12.2, 12.2, 20.0, 12.2, 20.0]

        nCols = 3
        self.info_widgets = []
        self.val_widgets = []
        self.widget_lookup = {}
        for i in range(len(self.info_strings)):
            self.info_widgets.append(QtWidgets.QLabel(self.info_strings[i]))
            self.val_widgets.append(QtWidgets.QLabel(str(int(self.info_vals[i]))))
            lower_layout.addWidget(self.info_widgets[-1], i // nCols, 2 * (i % nCols))
            lower_layout.addWidget(
                self.val_widgets[-1], i // nCols, 1 + 2 * (i % nCols)
            )
            self.widget_lookup[self.info_strings[i]] = i

        self.num_data_points = 1000
        self.time = np.arange(-1000, 0, 1)
        self.flow = (np.mod(self.time + i * 13, 100) / 10 - 2) * np.random.uniform(
            0.9, 1.1, len(self.time)
        )
        self.curr_bin = 999
        self.real_time = self.time[-1]  # for animation

    def set_plot(self, i):  # time, values, ok=True):
        # hardwire some error conditions
        isdead = i == 4
        if isdead:
            return
        ok = i % 7 != 1

        self.curr_bin = (self.curr_bin + 1) % self.num_data_points
        self.real_time += 1
        self.flow[self.curr_bin] = (
            (self.real_time + i * 13 % 100) / 10 - 2
        ) * np.random.uniform(0.9, 1.1, 1)

        pen = pg.mkPen(color=(0, 255, 0) if ok else (255, 0, 0), width=5)
        self.graph.plot(self.time, np.roll(self.flow, -1 * self.curr_bin), pen=pen)

        upper = pg.InfiniteLine(angle=0)
        upper.setPos([0, 10])

        lower = pg.InfiniteLine(angle=0)
        lower.setPos([0, -2])

        self.graph.addItem(upper)
        self.graph.addItem(lower)

        if ok:
            self.alert.status = Status.OK.name
        else:
            self.alert.status = Status.ALERT.name

        for key in self.widget_lookup:
            val = self.widget_lookup[key]
            v = np.random.uniform(5.0, 15.0)
            self.val_widgets[val].setText(str(int(v)))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setObjectName("MainWindow")

        pg.setConfigOptions(antialias=True)

        # self.graphs = QtWidgets.QVBoxLayout()
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setObjectName("maingrid")

        # Replace with proper importlib.resources if made a package
        with open("style.css") as f:
            self.setStyleSheet(f.read())

        self.setCentralWidget(self.centralwidget)

        self.centralwidget.setLayout(layout)

        self.graphs = [PatientSensor(i) for i in range(20)]
        for i, graph in enumerate(self.graphs):
            layout.addWidget(self.graphs[i], *reversed(divmod(i, 5)))
            graph.set_plot(i)

        self.qTimer = QTimer()
        self.qTimer.setInterval(1000)
        self.qTimer.timeout.connect(self.update_graphs)
        self.qTimer.start()

    def update_graphs(self):
        print("Calling")
        for i, graph in enumerate(self.graphs):
            graph.set_plot(i)


def main():
    import time

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
