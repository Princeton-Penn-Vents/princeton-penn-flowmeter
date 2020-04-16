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
import math
from datetime import datetime
from pathlib import Path
from string import Template

from processor.generator import Status
from processor.local_generator import LocalGenerator
from processor.remote_generator import RemoteGenerator

DIR = Path(__file__).parent.absolute()

guicolors = {
    "ALERT": QtGui.QColor(0, 0, 100),
    "DISCON": QtGui.QColor(0, 0, 200),
}


logging_directory = None


class GraphInfo:
    def __init__(self):
        # the y limits ought to be configurable.
        self.graph_labels = ["flow", "pressure", "volume"]

        self.graph_pens = {
            "flow": (120, 255, 50),
            "pressure": (255, 120, 50),
            "volume": (255, 128, 255),
        }

        self.graph_pen_qcol = {k: QtGui.QColor(*v) for k, v in self.graph_pens.items()}

        self.yLims = {"flow": (-40, 30), "pressure": (0, 20), "volume": (0, 800)}
        self.yTicks = {"flow": [-30, 0, 30], "pressure": [0, 15], "volume": [0, 750]}
        self.units = {"flow": "L/m", "pressure": "cm H2O", "volume": "mL"}


class NumberLabel(QtWidgets.QLabel):
    pass


class NumbersWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setLayout(layout)

        self.val_widgets = {}

        info_strings = [
            "RR",  # (breaths/min)
            "TVi",  # (mL)
            "TVe",  # (mL)
            "PIP",  # (cm H2O)
            "PEEP",  # (cm H2O)
        ]

        for info in info_strings:
            val_widget = NumberLabel("---")
            val_widget.setMinimumWidth(56)
            self.val_widgets[info] = val_widget
            layout.addRow(info, self.val_widgets[info])
            self.set_value(info, None)

    def set_value(self, info_str: str, value: float = None, ok: bool = True) -> None:
        val_widget = self.val_widgets[info_str]
        info_widget = self.layout().labelForField(val_widget)

        val_widget.setText("---" if value is None else f"{value:.0f}")

        prev = val_widget.property("measure")
        curr = "NONE" if value is None else ("OK" if ok else "ERR")

        if prev is None or prev != curr:
            val_widget.setProperty("measure", curr)
            info_widget.setProperty("measure", curr)
            val_widget.style().unpolish(val_widget)
            val_widget.style().polish(val_widget)
            info_widget.style().unpolish(info_widget)
            info_widget.style().polish(info_widget)

    def __iter__(self):
        return iter(self.val_widgets)


class AlertWidget(QtWidgets.QWidget):
    @property
    def status(self) -> Status:
        return Status[self.property("status")]

    @status.setter
    def status(self, value: Status):
        self.setProperty("status", value.name)
        self.name_btn.style().unpolish(self.name_btn)
        self.name_btn.style().polish(self.name_btn)

    def __init__(self, i: int):
        super().__init__()
        column_layout = QtWidgets.QVBoxLayout()
        self.setLayout(column_layout)

        self.name_btn = QtWidgets.QPushButton(str(i + 1))
        column_layout.addWidget(self.name_btn)

        self.values = NumbersWidget()
        column_layout.addWidget(self.values)


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

    def __init__(self, i, *args, ip, port, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_status_change = int(1000 * datetime.now().timestamp())
        self.label = i
        self.current_alarms = {}

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.graphview = GraphicsView(parent=self, i=i)
        graphlayout = pg.GraphicsLayout()
        graphlayout.setContentsMargins(0, 5, 0, 0)
        self.graphview.setCentralWidget(graphlayout)
        layout.addWidget(self.graphview)

        gis = GraphInfo()
        self.graph = {}
        for j, key in enumerate(gis.graph_labels):
            self.graph[key] = graphlayout.addPlot(x=[], y=[], name=key.capitalize())
            self.graph[key].setMouseEnabled(False, False)
            self.graph[key].invertX()
            if j != len(gis.graph_labels):
                graphlayout.nextRow()

        self.alert = AlertWidget(i)

        layout.addWidget(self.alert)

        if port is not None:
            if i == 7:  # hack to make this one always disconnected
                self.flow = RemoteGenerator()
            else:
                self.flow = RemoteGenerator(ip=ip, port=port + i)
        else:
            status = Status.OK if i % 7 != 1 else Status.ALERT
            if i == 7:
                status = Status.DISCON
            self.flow = LocalGenerator(status, logging=logging_directory)

        self.alert.status = self.flow.status
        self.alert.name_btn.clicked.connect(self.click_number)

    @Slot()
    def click_number(self):
        number, ok = QtWidgets.QInputDialog.getText(self, "Select port", "Pick a port")
        if ok:
            try:
                port = int(number)
            except ValueError:
                self.flow = LocalGenerator(Status.DISCON, logging=logging_directory)
                return
            self.flow = RemoteGenerator(port=port)

    def set_plot(self):
        self.flow.get_data()
        self.flow.analyze()

        gis = GraphInfo()

        self.curves = {}
        first_graph = self.graph[gis.graph_labels[0]]
        for i, (key, graph) in enumerate(self.graph.items()):
            pen = pg.mkPen(color=gis.graph_pens[key], width=2)
            self.curves[key] = graph.plot(
                self.flow.time, getattr(self.flow, key), pen=pen
            )

            graph.setRange(xRange=(30, 0), yRange=gis.yLims[key])
            dy = [(value, str(value)) for value in gis.yTicks[key]]
            graph.getAxis("left").setTicks([dy, []])
            if i != len(gis.graph_labels) - 1:
                graph.hideAxis("bottom")
            graph.addLine(y=0)

        self.graph[gis.graph_labels[0]].setXLink(self.graph[gis.graph_labels[1]])
        self.graph[gis.graph_labels[1]].setXLink(self.graph[gis.graph_labels[2]])

    @Slot()
    def update_plot(self):
        self.flow.get_data()
        self.flow.analyze()
        gis = GraphInfo()

        # Fill in the data
        for key in gis.graph_labels:
            self.curves[key].setData(self.flow.time, getattr(self.flow, key))

        t_now = int(1000 * datetime.now().timestamp())

        # Change of status requires a background color change
        if self.property("alert_status") != self.flow.status:
            self.setProperty("alert_status", self.flow.status.name)
            self.style().unpolish(self)
            self.style().polish(self)
        self.alert.status = self.flow.status

        alarming_quanities = {key.split()[0] for key in self.flow.alarms}

        for key in self.alert.values:
            self.alert.values.set_value(
                key,
                value=self.flow.cumulative.get(key),
                ok=key not in alarming_quanities,
            )


class PatientGrid(QtWidgets.QWidget):
    def __init__(self, *args, width, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Avoid wiggles when updating
        for i in range(width):
            layout.setColumnStretch(i, 3)

        self.setLayout(layout)


class MainStack(QtWidgets.QWidget):
    def __init__(self, *args, ip, port, refresh, displays, **kwargs):
        super().__init__(*args, **kwargs)

        height = math.ceil(math.sqrt(displays))
        width = math.ceil(displays / height)

        layout = QtWidgets.QVBoxLayout()
        if displays > 3:  # avoid adding this to small screens
            headerwidget = HeaderWidget(self)
            layout.addWidget(headerwidget)
        patientwidget = PatientGrid(self, width=width)
        layout.addWidget(patientwidget)

        self.setLayout(layout)

        self.graphs = [
            PatientSensor(i, ip=ip, port=port, parent=patientwidget)
            for i in range(displays)
        ]
        for i, graph in enumerate(self.graphs):
            patientwidget.layout().addWidget(
                self.graphs[i], *reversed(divmod(i, height))
            )
            graph.set_plot()

            graph.qTimer = QtCore.QTimer()
            graph.qTimer.setInterval(refresh)
            graph.qTimer.timeout.connect(graph.update_plot)
            graph.qTimer.start()

    def closeEvent(self):
        for graph in self.graphs:
            graph.flow.close()


class PrincetonLogoWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        logo = QPixmap("images/PUsig2-158C-shield.png").scaledToWidth(18)
        logolabel = QtWidgets.QLabel()
        logolabel.setPixmap(logo)

        text = QtWidgets.QLabel("     Princeton Open Vent Monitor")
        text.setAlignment(Qt.AlignLeft)
        layout.addWidget(logolabel, 0, Qt.AlignVCenter)
        layout.addWidget(text, 0, Qt.AlignVCenter)
        layout.addStretch()
        layout.setSpacing(0)
        self.setLayout(layout)


class NSFLogoWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        logo = QPixmap("images/nsf-logo-100.png").scaledToWidth(25)
        logolabel = QtWidgets.QLabel()
        logolabel.setPixmap(logo)
        layout.addWidget(logolabel, 0, Qt.AlignVCenter)
        layout.setAlignment(Qt.AlignRight)
        self.setLayout(layout)


class DateTimeWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        now = datetime.now()
        nowstring = now.strftime("%d %b %Y %H:%M:%S")
        text = QtWidgets.QLabel(nowstring)
        text.setFont(QtGui.QFont("Times", 20, QtGui.QFont.Bold))
        text.setStyleSheet("color: #F58025;")
        text.setAlignment(Qt.AlignLeft)
        layout.addWidget(text, 0, Qt.AlignVCenter)
        layout.addStretch()
        layout.setSpacing(0)
        self.setLayout(layout)


class GraphLabelWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        gis = GraphInfo()

        alpha = 140
        values = {}
        for key in gis.graph_pen_qcol:
            pen = gis.graph_pen_qcol[key]
            values[key] = "{r}, {g}, {b}, {a}".format(
                r=pen.red(), g=pen.green(), b=pen.blue(), a=alpha
            )

        text = QtWidgets.QLabel("Graph settings")
        text.setAlignment(Qt.AlignLeft)
        layout.addWidget(text, 1, Qt.AlignVCenter)
        self.buttons = {}

        for key in gis.graph_labels:
            name_btn = QtWidgets.QPushButton(
                key.capitalize() + "(" + gis.units[key] + ")"
            )
            name_btn.setProperty("graph", key)
            self.buttons[key] = name_btn
            layout.addWidget(name_btn, 1, Qt.AlignVCenter)
            name_btn.clicked.connect(self.click_graph_info)

        self.setLayout(layout)

    @Slot()
    def click_graph_info(self):
        # ok - this needs to get generalized and extended
        number, ok = QtWidgets.QInputDialog.getDouble(
            self, "Adjust plots", "Min Y axis", 10, 0, 100
        )
        if ok:
            try:
                print("Found number", number, ok)
            except ValueError:
                return


class HeaderWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        princeton_logo = PrincetonLogoWidget()
        graph_info = GraphLabelWidget()
        nsf_logo = NSFLogoWidget()
        # dt_info = DateTimeWidget()
        layout.addWidget(princeton_logo, 6)
        layout.addWidget(graph_info, 6)
        # layout.addWidget(dt_info, 6) # Would need to be updated periodically
        layout.addWidget(nsf_logo, 2)

        self.setLayout(layout)

    @Slot()
    def click_header(self):
        number, ok = QtWidgets.QInputDialog.getText(self, "Select port", "Pick a port")
        if ok:
            try:
                port = int(number)
            except ValueError:
                return
            print("hi there", number)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, ip, port, refresh, displays, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("MainWindow")

        # May be expensive, probably only enable if we multithread the draw
        # pg.setConfigOptions(antialias=True)
        pg.setConfigOption("background", (0, 0, 0, 0))

        # Replace with proper importlib.resources if made a package
        gis = GraphInfo()
        with open(DIR / "nurse" / "style.css") as f:
            s = Template(f.read())
            t = s.substitute(**gis.graph_pens)
            self.setStyleSheet(t)

        centralwidget = MainStack(
            self, *args, ip=ip, port=port, refresh=refresh, displays=displays, **kwargs
        )
        self.setCentralWidget(centralwidget)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.centralWidget().closeEvent()
        super().closeEvent(event)


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
        main.resize(min(1920, size.width()), min(1080, size.height()))
        main.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--ip", default="127.0.0.1", help="Select an ip address")
    parser.add_argument(
        "--refresh", default=1000, type=int, help="Screen refresh timer, in ms"
    )
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
        "--logging",
        default="",
        help="If a directory name, local generators fill *.dat files in that directory with time-series (time, flow, pressure)",
    )

    arg, unparsed_args = parser.parse_known_args()
    if arg.logging != "":
        logging_directory = arg.logging

    main(
        argv=sys.argv[:1] + unparsed_args,
        ip=arg.ip,
        port=arg.port,
        fullscreen=arg.fullscreen,
        displays=arg.displays,
        refresh=arg.refresh,
    )
