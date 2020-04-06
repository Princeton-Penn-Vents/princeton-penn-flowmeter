#!/usr/bin/env python3

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import pyqtSlot as Slot  # Named like PySide
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


class LocalGenerator:
    def __init__(self, status: Status):
        self.status = status
        self.time = np.linspace(-1000, 0, 1000)
        self.current = 0
        self.random = np.random.uniform(0.9, 1.1, len(self.time))

    def calc_flow(self):
        v = (
            (np.mod(self.time + self.current, 100) / 10 - 2)
            * self.random
            * (0.6 if self.status == Status.ALERT else 1)
        )
        if self.status == Status.DISCON:
            v[-min(self.current, len(self.time)) :] = 0
        return v

    def tick(self):
        self.current += 5
        self.random = np.roll(self.random, 5)


class AlertWidget(QtWidgets.QWidget):
    def status(self):
        return Status[self.property("status")]

    def pstatus(self, value):
        self.alert.setText(value.name)
        self.setProperty("status", value.name)

    def __init__(self, i: int):
        super().__init__()
        column_layout = QtWidgets.QVBoxLayout()
        self.setLayout(column_layout)

        name = QtWidgets.QLabel(str(i + 1))
        name.setAlignment(QtCore.Qt.AlignCenter)
        column_layout.addWidget(name)

        self.alert = QtWidgets.QLabel("DISCON")
        self.alert.setAlignment(QtCore.Qt.AlignCenter)
        column_layout.addWidget(self.alert)


class PatientSensor(QtWidgets.QWidget):
    def __init__(self, i):
        super().__init__()

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
        # Time inferred
        # self.graph.setLabel("bottom", "Time", units="seconds")
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
        for j in range(len(self.info_strings)):
            self.info_widgets.append(QtWidgets.QLabel(self.info_strings[j]))
            self.val_widgets.append(QtWidgets.QLabel(str(int(self.info_vals[j]))))
            lower_layout.addWidget(self.info_widgets[-1], j // nCols, 2 * (j % nCols))
            lower_layout.addWidget(
                self.val_widgets[-1], j // nCols, 1 + 2 * (j % nCols)
            )
            self.widget_lookup[self.info_strings[j]] = j

        status = Status.OK if i % 7 != 1 else Status.ALERT
        if i == 4:
            status = Status.DISCON
        self.alert.pstatus(status)
        self.flow = LocalGenerator(status)

    def set_plot(self):
        color = {
            Status.OK: (151, 222, 121),
            Status.ALERT: (237, 67, 55),
            Status.DISCON: (50, 50, 220),
        }[self.alert.status()]

        pen = pg.mkPen(color=color, width=5)
        self.curve = self.graph.plot(self.flow.time, self.flow.calc_flow(), pen=pen)
        self.graph.setRange(xRange=(-1000, 0), yRange=(-3, 10))

        pen = pg.mkPen(color=(220, 220, 50), width=3)

        upper = pg.InfiniteLine(angle=0, pen=pen)
        upper.setPos([0, 8])
        self.graph.addItem(upper)

        lower = pg.InfiniteLine(angle=0, pen=pen)
        lower.setPos([0, -2])
        self.graph.addItem(lower)

    @Slot()
    def update_plot(self):
        self.flow.tick()
        self.curve.setData(self.flow.time, self.flow.calc_flow())

        for key in self.widget_lookup:
            val = self.widget_lookup[key]
            v = np.random.uniform(5.0, 15.0)
            self.val_widgets[val].setText(str(int(v)))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setObjectName("MainWindow")

        pg.setConfigOptions(antialias=True)

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
            graph.set_plot()

            graph.qTimer = QtCore.QTimer()
            graph.qTimer.setInterval(1000)
            graph.qTimer.timeout.connect(graph.update_plot)
            graph.qTimer.start()


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
