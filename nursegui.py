#!/usr/bin/env python3

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSlot as Slot  # Named like PySide
import pyqtgraph as pg
import numpy as np
import sys
import os
import enum
import json
import requests
from pathlib import Path

DIR = Path(__file__).parent.absolute()


class Status(enum.Enum):
    OK = enum.auto()
    ALERT = enum.auto()
    DISCON = enum.auto()


COLOR = {
    Status.OK: (151, 222, 121),
    Status.ALERT: (237, 67, 55),
    Status.DISCON: (50, 50, 220),
}


class LocalGenerator:
    def __init__(self, status: Status):
        self.status = status
        self.current = 0
        ramp=np.array([0.1,  0.8807970779778823, 0.96, 0.9975273768433653, 0.9996646498695336])
        decay=-1.0 * np.exp(-1.0 * np.arange(0,3,0.03))
        breath = 10 * np.concatenate((ramp,np.full(35,1),np.flip(ramp), -1.0*ramp,decay))
        self.flow = np.concatenate((breath,breath,breath,breath,breath,breath))
        self.flow = self.flow * np.random.uniform(0.98, 1.02, len(self.flow))
        self.time = np.arange(0,len(self.flow),1)
        self.axistime = -1.0 * self.time / 50  # ticks per second

    def calc_flow(self):
        #v = (
        #    (np.mod(self.time + self.current, 100) / 10 - 2)
        #    * self.random
        #    * (0.6 if self.status == Status.ALERT else 1)
        #)
        v = (
            self.flow
            * (0.6 if self.status == Status.ALERT else 1)
        )
        if self.status == Status.DISCON:
            v[-min(self.current, len(self.time)) :] = 0
        return self.axistime, v

    def tick(self):
        self.current += 10
        self.flow = np.roll(self.flow, 10)

class DisconGenerator:
    status = Status.DISCON

    def calc_flow(self):
        return [], []

    def tick(self):
        pass


class RemoteGenerator:
    def tick(self):
        pass

    def __init__(self, ip="127.0.0.1", port="8123"):
        self.ip = ip
        self.port = port
        self.status = Status.OK

    def calc_flow(self):
        try:
            r = requests.get(f"http://{self.ip}:{self.port}")
        except requests.exceptions.ConnectionError:
            self.status = Status.DISCON
            return [], []

        root = json.loads(r.text)
        time = np.asarray(root["data"]["timestamps"])
        flow = np.asarray(root["data"]["flows"])

        return time, flow


class AlertWidget(QtWidgets.QWidget):
    @property
    def status(self):
        return Status[self.property("status")]

    @status.setter
    def status(self, value):
        self.alert.setText(value.name if value != Status.OK else "")
        self.setProperty("status", value.name)
        self.alert.style().unpolish(self.alert)
        self.alert.style().polish(self.alert)

    def __init__(self, i: int):
        super().__init__()
        column_layout = QtWidgets.QVBoxLayout()
        self.setLayout(column_layout)

        self.name_btn = QtWidgets.QPushButton(str(i + 1))
        column_layout.addWidget(self.name_btn, 2)

        self.alert = QtWidgets.QLabel("DISCON")
        self.alert.setAlignment(QtCore.Qt.AlignCenter)
        column_layout.addWidget(self.alert, 2)

        column_layout.addStretch(6)



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

        graphview = pg.GraphicsView(parent=self)
        graphlayout = pg.GraphicsLayout()
        graphlayout.setContentsMargins(0, 0, 0, 0)
        graphview.setCentralWidget(graphlayout)

        layout.addWidget(graphview, 7)

        self.graph_flow = graphlayout.addPlot(x=[], y=[], name="Flow")
        self.graph_flow.setLabel("left", "F", units="L/m")
        self.graph_flow.setMouseEnabled(False, False)

        graphlayout.nextRow()

        self.graph_pressure = graphlayout.addPlot(x=[], y=[], name="Pressure")
        self.graph_pressure.setLabel("left", "P", units="cm/w")
        self.graph_pressure.setMouseEnabled(False, False)

        graphlayout.nextRow()

        self.graph_volume = graphlayout.addPlot(x=[], y=[], name="Volume")
        self.graph_volume.setLabel("left", "V", units="L")
        self.graph_volume.setMouseEnabled(False, False)


        self.alert = AlertWidget(i)
        layout.addWidget(self.alert, 3)

        lower = QtWidgets.QWidget()
        outer_layout.addWidget(lower)
        lower_layout = QtWidgets.QGridLayout()
        lower.setLayout(lower_layout)

        self.info_strings = [
            "Something (L/m):",
            "AveMinFlow (L/m):",
            "AveFlow (L/m):",
            "CurrentFlow (L/m):",
        ]

        # dummy
        self.info_vals = [12.2, 20.0, 12.2, 20.0]

        nCols = 2
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
            self.flow = DisconGenerator()
        elif i == 3:
            self.flow = RemoteGenerator()
        else:
            self.flow = LocalGenerator(status)

        self.alert.status = self.flow.status
        self.alert.name_btn.clicked.connect(self.click_number)

    @Slot()
    def click_number(self):
        number, ok = QtWidgets.QInputDialog.getText(self, "Select port", "Pick a port")
        if ok:
            try:
                port = int(number)
            except ValueError:
                self.flow = DisconGenerator()
                return
            self.flow = RemoteGenerator(port=port)

    def set_plot(self):
        pen = pg.mkPen(color=(120, 255, 50), width=2)
        self.curve_flow = self.graph_flow.plot(*self.flow.calc_flow(), pen=pen)
        pen = pg.mkPen(color=(255, 120, 50), width=2)
        self.curve_pressure = self.graph_pressure.plot(*self.flow.calc_flow(), pen=pen)
        pen = pg.mkPen(color=(50, 120, 255), width=2)
        self.curve_volume = self.graph_volume.plot(*self.flow.calc_flow(), pen=pen)
        # self.graph_flow.setRange(xRange=(-1000, 0), yRange=(-3, 10))

        self.graph_flow.setXLink(self.graph_pressure)
        self.graph_flow.setXLink(self.graph_volume)
        self.graph_flow.hideAxis('bottom')
        self.graph_pressure.hideAxis('bottom')

        pen = pg.mkPen(color=(220, 220, 50), width=3)

        #self.upper = self.graph_flow.addLine(y=8, pen=pen)
        #self.lower = self.graph_flow.addLine(y=-2, pen=pen)

    @Slot()
    def update_plot(self):
        self.flow.tick()
        self.curve_flow.setData(*self.flow.calc_flow())
        self.curve_pressure.setData(*self.flow.calc_flow())
        self.curve_volume.setData(*self.flow.calc_flow())
        self.alert.status = self.flow.status

        for key in self.widget_lookup:
            val = self.widget_lookup[key]
            v = np.random.uniform(5.0, 15.0)
            self.val_widgets[val].setText(str(int(v)))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setObjectName("MainWindow")
        self.resize(1920, 1080)

        # May be expensive, probably only enable if we multithread the draw
        # pg.setConfigOptions(antialias=True)

        layout = QtWidgets.QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Avoid wiggles when updating
        for i in range(4):
            layout.setColumnStretch(i, 3)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setObjectName("maingrid")

        # Replace with proper importlib.resources if made a package
        with open(DIR / "nurse" / "style.css") as f:
            self.setStyleSheet(f.read())

        self.setCentralWidget(self.centralwidget)

        self.centralwidget.setLayout(layout)

        self.graphs = [PatientSensor(i) for i in range(20)]
        for i, graph in enumerate(self.graphs):
            layout.addWidget(self.graphs[i], *reversed(divmod(i, 4)))
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
