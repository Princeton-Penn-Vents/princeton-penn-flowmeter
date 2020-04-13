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
from pathlib import Path

from nurse.generator import Status
from nurse.local_generator import LocalGenerator
from nurse.remote_generator import RemoteGenerator

DIR = Path(__file__).parent.absolute()

guicolors = {"ALERT": QtGui.QColor(0, 0, 205), "patient_border": "rgb(160,200,255)"}

logging_directory = None


class GraphInfo:
    def __init__(self):
        # the y limits ought to be configurable.
        self.graph_labels = ["flow", "pressure", "volume"]
        self.graph_pens = {}
        self.graph_pens["flow"] = (120, 255, 50)
        self.graph_pens["pressure"] = (255, 120, 50)
        self.graph_pens["volume"] = (255, 128, 255)

        self.graph_pen_qcol = {}
        for key in self.graph_pens:
            self.graph_pen_qcol[key] = QtGui.QColor(
                self.graph_pens[key][0],
                self.graph_pens[key][1],
                self.graph_pens[key][2],
            )

        self.yLims = {}
        self.yLims["flow"] = (-30, 30)
        self.yLims["pressure"] = (0, 20)
        self.yLims["volume"] = (0, 800)

        self.yTicks = {}
        self.yTicks["flow"] = [-25, 0, 25]
        self.yTicks["pressure"] = [0, 15]
        self.yTicks["volume"] = [0, 750]

        self.units = {}
        self.units["flow"] = "L/m"
        self.units["pressure"] = "cm H2O"
        self.units["volume"] = "mL"


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

        self.name_btn = QtWidgets.QPushButton(str(i + 1))
        column_layout.addWidget(self.name_btn)  # , 2)

        self.info_strings = [
            "RR",  # (breaths/min)
            "TVe",  # (mL)
            "TVi",  # (mL)
            "PIP",  # (cm H2O)
            "PEEP",  # (cm H2O)
        ]

        lower = QtWidgets.QWidget()
        lower_layout = QtWidgets.QGridLayout()
        lower_layout.setContentsMargins(0, 0, 0, 0)
        lower_layout.setColumnMinimumWidth(1, 20)  # big enough - maybe too big?
        lower_layout.setVerticalSpacing(0)
        lower_layout.setSpacing(0)

        lower.setLayout(lower_layout)
        # Values seen before cumulative average values available
        self.info_vals = [0, 0, 0, 0, 0] 

        self.info_widgets = []
        self.val_widgets = []
        self.widget_lookup = {}
        for j in range(len(self.info_strings)):
            self.info_widgets.append(QtWidgets.QLabel(self.info_strings[j]))
            self.val_widgets.append(QtWidgets.QLabel(str(int(self.info_vals[j]))))
            self.info_widgets[-1].setContentsMargins(0, 0, 0, 0)
            self.val_widgets[-1].setContentsMargins(0, 0, 0, 0)
            self.val_widgets[-1].setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.widget_lookup[self.info_strings[j]] = j
            lower_layout.addWidget(self.info_widgets[-1], j, 0)
            lower_layout.addWidget(self.val_widgets[-1], j, 1)

        column_layout.addWidget(lower)


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
        self.setObjectName("PatientInfo")
        self.setStyleSheet(
            "#PatientInfo { border: 1px solid " + guicolors["patient_border"] + " }"
        )  # borders

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.graphview = GraphicsView(parent=self, i=i)
        self.graphview.setObjectName("GraphView")
        graphlayout = pg.GraphicsLayout()
        graphlayout.setContentsMargins(0, 0, 0, 0)
        self.graphview.setCentralWidget(graphlayout)
        layout.addWidget(self.graphview)  # , 7)

        gis = GraphInfo()
        for j, key in enumerate(gis.graph_labels):
            attr_name = "graph_" + key
            setattr(
                self, attr_name, graphlayout.addPlot(x=[], y=[], name=key.capitalize())
            )
            getattr(self, attr_name).setMouseEnabled(False, False)
            getattr(self, attr_name).invertX()
            if j != len(gis.graph_labels):
                graphlayout.nextRow()

        self.alert = AlertWidget(i)

        layout.addWidget(self.alert)  # , 3)

        status = Status.OK if i % 7 != 1 else Status.ALERT

        if port is not None:
            self.flow = RemoteGenerator(ip=ip, port=port + i)
        else:
            self.flow = LocalGenerator(status, logging=logging_directory)

        self.alert.status = self.flow.status

        if self.alert.status == Status.ALERT:
            self.graphview.setBackground(guicolors["ALERT"])

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
        first_graph = getattr(self, "graph_" + gis.graph_labels[0])
        for i, key in enumerate(gis.graph_labels):
            graph = getattr(self, "graph_" + key)
            pen = pg.mkPen(color=gis.graph_pens[key], width=2)
            self.curves[key] = graph.plot(
                self.flow.time, getattr(self.flow, key), pen=pen
            )

            graph.setRange(xRange=(30, 0), yRange=gis.yLims[key])
            dy = [(value, str(value)) for value in gis.yTicks[key]]
            graph.getAxis("left").setTicks([dy, []])
            if i != len(gis.graph_labels) - 1:
                graph.hideAxis("bottom")
            if i != 0:
                first_graph.setXLink(graph)
            graph.addLine(y=0)

    @Slot()
    def update_plot(self):
        self.flow.get_data()
        self.flow.analyze()
        gis = GraphInfo()

        for i, key in enumerate(gis.graph_labels):
            graph = getattr(self, "graph_" + key)
            self.curves[key].setData(self.flow.time, getattr(self.flow, key))

        # look for status changes
        # useful for standalone testing
        # import random
        # if random.random()<0.1:
        #    self.flow.status=Status.ALERT
        # else:
        #    self.flow.status=Status.OK
        if self.flow.status != self.alert.status:
            self.alert.status = self.flow.status

            if self.alert.status == Status.ALERT:
                self.graphview.setBackground(guicolors["ALERT"])
            else:
                self.graphview.setBackground(QtGui.QColor(0, 0, 0))
            #TESTself.graphview.setBackground(guicolors["ALERT"])

        for key in self.alert.widget_lookup:
            valindex = self.alert.widget_lookup[key]
            #val = self.flow.cumulative[key]            
            val = self.flow.cumulative.get(key)
            if val: 
                self.alert.val_widgets[valindex].setText(str(int(round(val))))
            else:
                self.alert.val_widgets[valindex].setText('---')
            

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
        text.setFont(QtGui.QFont("Times", 20, QtGui.QFont.Bold))
        text.setStyleSheet("color: #F58025;")
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
        text.setFont(QtGui.QFont("Times", 18, QtGui.QFont.Bold))
        text.setStyleSheet("QLabel { color: ghostwhite }")
        text.setAlignment(Qt.AlignLeft)
        layout.addWidget(text, 1, Qt.AlignVCenter)
        self.buttons = {}

        for key in gis.graph_labels:
            name_btn = QtWidgets.QPushButton(
                key.capitalize() + "(" + gis.units[key] + ")"
            )
            name_btn.setFont(QtGui.QFont("Times", 18, QtGui.QFont.Bold))
            name_btn.setStyleSheet(
                "QPushButton { background-color: 'transparent'; color: rgba("
                + values[key]
                + "); }"
            )
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
        layout.addWidget(princeton_logo, 6)
        layout.addWidget(graph_info, 6)
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

        if displays > 4:
            self.resize(1920, 1080)

        # May be expensive, probably only enable if we multithread the draw
        # pg.setConfigOptions(antialias=True)
        pg.setConfigOption("background", (0, 0, 0, 0))

        # Replace with proper importlib.resources if made a package
        with open(DIR / "nurse" / "style.css") as f:
            self.setStyleSheet(f.read())

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
        "--no-display", action="store_true", help="Prevents the main window from appearing; for debugging"
    )
    parser.add_argument(
        "--displays",
        "-n",
        type=int,
        default=20,
        help="# of displays, currently not dynamic",
    )
    parser.add_argument(
        "--logging", default="", help="If a directory name, local generators fill *.dat files in that directory with time-series (time, flow, pressure)"
    )

    arg, unparsed_args = parser.parse_known_args()
    if arg.logging != "":
        logging_directory = arg.logging

    main(
        argv=sys.argv[:1] + unparsed_args,
        ip=arg.ip,
        port=arg.port,
        fullscreen=arg.fullscreen,
        no_display=arg.no_display,
        displays=arg.displays,
        refresh=arg.refresh,
    )
