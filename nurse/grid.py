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
)

from nurse.common import guicolors, prefill, GraphInfo

from processor.generator import Status
from processor.local_generator import LocalGenerator
from processor.remote_generator import RemoteGenerator


class NumberLabel(QtWidgets.QLabel):
    pass


class NumbersWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = FormLayout()
        self.setLayout(layout)

        self.val_widgets = {}

        info_strings = [
            "RR",  # (breaths/min)
            "TVe",  # (mL)
            "PIP",  # (cm H2O)
            "PEEP",  # (cm H2O)
            "I:E time ratio",
        ]

        for info in info_strings:
            val_widget = NumberLabel("---")
            val_widget.setMinimumWidth(56)
            self.val_widgets[info] = val_widget
            layout.addRow(info.split()[0], self.val_widgets[info])
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


class PatientTitleWidget(QtWidgets.QWidget):
    def __init__(self, i: int):
        super().__init__()

        layout = HBoxLayout()
        self.setLayout(layout)

        self.name_btn = QtWidgets.QPushButton(f"{i+1}:")
        layout.addWidget(self.name_btn)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setText(prefill[i] if i < 20 else f"Patient {i+1}")
        layout.addWidget(self.name_edit)

    def repolish(self):
        self.name_btn.style().unpolish(self.name_btn)
        self.name_btn.style().polish(self.name_btn)

        self.name_edit.style().unpolish(self.name_edit)
        self.name_edit.style().polish(self.name_edit)


class GraphicsView(pg.GraphicsView):
    def __init__(self, *args, i, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_plot = i
        self.i = i

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.parent().parent().parent().parent().drilldown_activate(self.i)


class PatientSensor(QtGui.QFrame):
    @property
    def status(self):
        return Status[self.property("alert_status")]

    @status.setter
    def status(self, value: Status):
        self.setProperty("alert_status", value.name)
        self.title_widget.repolish()

    def __init__(self, i, *args, gen, logging=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_status_change = int(1000 * datetime.now().timestamp())
        self.label = i
        self.gen = gen
        self.current_alarms = {}
        self.logging = logging

        layout = HBoxLayout()
        self.setLayout(layout)

        layout_left = VBoxLayout()
        layout.addLayout(layout_left)

        self.title_widget = PatientTitleWidget(i)
        layout_left.addWidget(self.title_widget)

        self.graphview = GraphicsView(parent=self, i=i)
        graphlayout = pg.GraphicsLayout()
        graphlayout.setContentsMargins(0, 5, 0, 0)
        self.graphview.setCentralWidget(graphlayout)
        layout_left.addWidget(self.graphview)

        gis = GraphInfo()
        self.graph = {}
        for j, key in enumerate(gis.graph_labels):
            self.graph[key] = graphlayout.addPlot(x=[], y=[], name=key.capitalize())
            self.graph[key].setMouseEnabled(False, False)
            self.graph[key].invertX()
            if j != len(gis.graph_labels):
                graphlayout.nextRow()

        self.status = self.gen.status
        self.title_widget.name_btn.clicked.connect(self.click_number)

        self.values = NumbersWidget()
        layout.addWidget(self.values)

    @Slot()
    def click_number(self):
        number, ok = QtWidgets.QInputDialog.getText(self, "Select port", "Pick a port")
        if ok:
            try:
                port = int(number)
            except ValueError:
                self.gen = LocalGenerator(Status.DISCON, logging=self.logging)
                return
            self.gen = RemoteGenerator(port=port)

    def set_plot(self):

        gis = GraphInfo()

        self.curves = {}
        for i, (key, graph) in enumerate(self.graph.items()):
            pen = pg.mkPen(color=gis.graph_pens[key], width=2)

            self.curves[key] = graph.plot([], [], pen=pen)

            graph.setRange(xRange=(15, 0), yRange=gis.yLims[key])
            dy = [(value, str(value)) for value in gis.yTicks[key]]
            graph.getAxis("left").setTicks([dy, []])
            if i != len(gis.graph_labels) - 1:
                graph.hideAxis("bottom")
            graph.addLine(y=0)

        self.graph[gis.graph_labels[0]].setXLink(self.graph[gis.graph_labels[1]])
        self.graph[gis.graph_labels[1]].setXLink(self.graph[gis.graph_labels[2]])

    @Slot()
    def update_plot(self):
        tic = time.monotonic()
        gis = GraphInfo()

        with self.gen.lock:
            self.gen.get_data()
            ana = self.gen.analyze_as_needed()

            # Fill in the data
            for key in gis.graph_labels:
                if self.isVisible():
                    select = self.gen.time < 15 if len(self.gen.time) else slice(None)
                    self.curves[key].setData(
                        self.gen.time[select], getattr(self.gen, key)[select]
                    )
                else:
                    self.curves[key].setData([], [])

            if ana:
                # Change of status requires a background color change
                if self.property("alert_status") != self.gen.status:
                    self.setProperty("alert_status", self.gen.status.name)
                    self.style().unpolish(self)
                    self.style().polish(self)

                self.status = self.gen.status

                alarming_quanities = {key.split()[0] for key in self.gen.alarms}

                for key in self.values:
                    self.values.set_value(
                        key,
                        value=self.gen.cumulative.get(key),
                        ok=key not in alarming_quanities,
                    )

        toc = time.monotonic()
        t = (toc - tic) * (len(self.parent().graphs) + 1)
        guess_each = int(t * 1000 * 1.1) + 20

        if not self.isVisible():
            guess_each += 1000

        self.qTimer.start(max(guess_each, 50))
