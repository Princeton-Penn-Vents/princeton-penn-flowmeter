#!/usr/bin/env python3

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSlot as Slot  # Named like PySide

import pyqtgraph as pg

# stdlib
import argparse
import numpy as np
import os
import sys
from pathlib import Path

from nurse.generator import Status, LocalGenerator, RemoteGenerator

DIR = Path(__file__).parent.absolute()

COLOR = {
    Status.OK: (151, 222, 121),
    Status.ALERT: (237, 67, 55),
    Status.DISCON: (50, 50, 220),
}


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


class GraphicsView(pg.GraphicsView):
    def __init__(self, *args, i, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_plot = i

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            print(f"Clicked {self.current_plot + 1}")


class PatientSensor(QtWidgets.QWidget):
    def __init__(self, i, *, ip, port):
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

        graphview = GraphicsView(parent=self, i=i)
        graphlayout = pg.GraphicsLayout()
        graphlayout.setContentsMargins(0, 0, 0, 0)
        graphview.setCentralWidget(graphlayout)

        layout.addWidget(graphview, 7)

        self.graph_flow = graphlayout.addPlot(x=[], y=[], name="Flow")
        self.graph_flow.setLabel("left", "F", units="L/m")
        self.graph_flow.setMouseEnabled(False, False)
        self.graph_flow.invertX()

        graphlayout.nextRow()

        self.graph_pressure = graphlayout.addPlot(x=[], y=[], name="Pressure")
        self.graph_pressure.setLabel("left", "P", units="cm/w")
        self.graph_pressure.setMouseEnabled(False, False)
        self.graph_pressure.invertX()

        graphlayout.nextRow()

        self.graph_volume = graphlayout.addPlot(x=[], y=[], name="Volume")
        self.graph_volume.setLabel("left", "V", units="mL")
        self.graph_volume.setMouseEnabled(False, False)
        self.graph_volume.invertX()

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

        if port is not None:
            self.flow = RemoteGenerator(ip=ip, port=port + i)
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
        # self.graph_flow.setRange(xRange=(-1000, 0), yRange=(-3, 10))

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

        for key in self.widget_lookup:
            val = self.widget_lookup[key]
            v = np.random.uniform(5.0, 15.0)
            self.val_widgets[val].setText(str(int(v)))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, ip, port, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setObjectName("MainWindow")
        self.resize(1920, 1080)

        # May be expensive, probably only enable if we multithread the draw
        # pg.setConfigOptions(antialias=True)

        layout = QtWidgets.QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Avoid wiggles when updating
        for i in range(5):
            layout.setColumnStretch(i, 3)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setObjectName("maingrid")

        # Replace with proper importlib.resources if made a package
        with open(DIR / "nurse" / "style.css") as f:
            self.setStyleSheet(f.read())

        self.setCentralWidget(self.centralwidget)

        self.centralwidget.setLayout(layout)

        self.graphs = [PatientSensor(i, ip=ip, port=port) for i in range(20)]
        for i, graph in enumerate(self.graphs):
            layout.addWidget(self.graphs[i], *reversed(divmod(i, 4)))
            graph.set_plot()

            graph.qTimer = QtCore.QTimer()
            graph.qTimer.setInterval(1000)
            graph.qTimer.timeout.connect(graph.update_plot)
            graph.qTimer.start()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()


def main(argv, *, ip, port, fullscreen):
    app = QtWidgets.QApplication(argv)
    main = MainWindow(ip=ip, port=port)
    if fullscreen:
        main.showFullScreen()
    else:
        main.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="Select an ip address")
    parser.add_argument(
        "--port", type=int, help="Select a starting port (8100 recommended)"
    )
    parser.add_argument("--fullscreen", action="store_true")
    arg, unparsed_args = parser.parse_known_args()
    main(
        argv=sys.argv[:1] + unparsed_args,
        ip=arg.ip,
        port=arg.port,
        fullscreen=arg.fullscreen,
    )
