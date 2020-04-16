import pyqtgraph as pg

import math
from datetime import datetime
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
)

from nurse.common import guicolors, prefill, GraphInfo

from processor.generator import Status


class DrillDownWidget(QtWidgets.QWidget):
    def __init__(self, *, refresh):
        super().__init__()
        self.gen = None

        layout = VBoxLayout()
        self.setLayout(layout)

        upper_bar = HBoxLayout()
        layout.addLayout(upper_bar)

        upper_bar.addWidget(QtWidgets.QLabel("Princeton Open Vent Monitor"))
        upper_bar.addWidget(QtWidgets.QPushButton("Mode: Scroll"))
        self.return_btn = QtWidgets.QPushButton("Return")
        upper_bar.addWidget(self.return_btn)

        self.graphview = pg.GraphicsView(parent=self)
        graphlayout = pg.GraphicsLayout()

        self.graphview.setCentralWidget(graphlayout)
        layout.addWidget(self.graphview)

        gis = GraphInfo()
        self.graph = {}
        for j, key in enumerate(gis.graph_labels):
            self.graph[key] = graphlayout.addPlot(x=[], y=[], name=key.capitalize())
            self.graph[key].invertX()
            if j != len(gis.graph_labels):
                graphlayout.nextRow()

        self.set_plot()

        self.qTimer = QtCore.QTimer()
        self.qTimer.setInterval(refresh)
        self.qTimer.timeout.connect(self.update_plot)
        self.qTimer.start()

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

            # Fill in the data
            for key in gis.graph_labels:
                self.curves[key].setData(self.gen.time, getattr(self.gen, key))
