import pyqtgraph as pg

import math
from datetime import datetime
from string import Template
import time

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

from nurse.common import guicolors, prefill, GraphInfo
from nurse.header import HeaderWidget, PrincetonLogoWidget

from processor.generator import Status


class DrilldownHeaderWidget(HeaderWidget):
    def __init__(self):
        super().__init__()
        layout = HBoxLayout()
        self.setLayout(layout)

        layout.addWidget(PrincetonLogoWidget())
        layout.addStretch()
        layout.addWidget(QtWidgets.QPushButton("Mode: Scroll"))
        layout.addStretch()
        self.return_btn = QtWidgets.QPushButton("Return to main view")
        self.return_btn.setObjectName("return_btn")
        layout.addWidget(self.return_btn)


class DrilldownWidget(QtWidgets.QWidget):
    @property
    def gen(self):
        return self.patient.gen

    @gen.setter
    def gen(self, value):
        self.patient.gen = value

    @property
    def graphs(self):
        return self.parent().main_stack.graphs

    def __init__(self, *, parent):
        super().__init__(parent=parent)

        layout = VBoxLayout()
        self.setLayout(layout)

        header = DrilldownHeaderWidget()
        self.return_btn = header.return_btn
        layout.addWidget(header)

        columns_layout = HBoxLayout()
        layout.addLayout(columns_layout)

        self.patient = PatientDrilldownWidget()
        columns_layout.addWidget(self.patient)

        side_layout = VBoxLayout()
        columns_layout.addLayout(side_layout)

        grid_layout = GridLayout()
        side_layout.addLayout(grid_layout)
        side_layout.addStretch()

        for i, gen in enumerate(self.graphs):
            grid_layout.addWidget(AlarmBox(i, gen=gen), *divmod(i, 2))


class AlarmBox(QtWidgets.QPushButton):
    def __init__(self, i, *, gen):
        super().__init__(str(i))


class PatientDrilldownWidget(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.gen = None

        layout = HBoxLayout()
        self.setLayout(layout)

        left_layout = VBoxLayout()
        layout.addLayout(left_layout)

        right_layout = VBoxLayout()
        layout.addLayout(right_layout)

        self.graphview = pg.GraphicsView(parent=self)
        graphlayout = pg.GraphicsLayout()

        self.graphview.setCentralWidget(graphlayout)
        left_layout.addWidget(self.graphview)

        gis = GraphInfo()
        self.graph = {}
        for j, key in enumerate(gis.graph_labels):
            self.graph[key] = graphlayout.addPlot(x=[], y=[], name=key.capitalize())
            self.graph[key].invertX()
            self.graph[key].setRange(xRange=(30, 0))
            if j != len(gis.graph_labels):
                graphlayout.nextRow()

        self.set_plot()

        left_layout.addWidget(QtWidgets.QLabel("Alarm settings"))
        right_layout.addWidget(QtWidgets.QLabel("Extra plot and settings"))

        self.qTimer = QtCore.QTimer()
        self.qTimer.setSingleShot(True)
        self.qTimer.timeout.connect(self.update_plot)

    def set_plot(self):

        gis = GraphInfo()
        self.curves = {}

        for i, (key, graph) in enumerate(self.graph.items()):
            pen = pg.mkPen(color=gis.graph_pens[key], width=2)
            self.curves[key] = graph.plot([], [], pen=pen)
            graph.addLine(y=0)

        self.graph[gis.graph_labels[0]].setXLink(self.graph[gis.graph_labels[1]])
        self.graph[gis.graph_labels[1]].setXLink(self.graph[gis.graph_labels[2]])

    @Slot()
    def update_plot(self):
        if self.isVisible() and self.gen is not None:
            gis = GraphInfo()
            tic = time.monotonic()

            with self.gen.lock:
                self.gen.get_data()
                self.gen.analyze_as_needed()

                # Fill in the data
                for key in gis.graph_labels:
                    self.curves[key].setData(self.gen.time, getattr(self.gen, key))

            toc = time.monotonic()
            t = toc - tic
            guess_each = int(t * 1000 * 1.1) + 30

            self.qTimer.start(max(guess_each, 100))
