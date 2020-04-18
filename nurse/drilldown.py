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


class PatientTitle(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = HBoxLayout()
        self.setLayout(layout)

        self.name_lbl = QtWidgets.QLabel("X")
        layout.addWidget(self.name_lbl)

        self.name_edit = QtWidgets.QLineEdit()
        layout.addWidget(self.name_edit)

    def activate(self, number: str, mirror: QtWidgets.QLineEdit):
        self.name_lbl.setText(number)
        self.name_edit.setText(mirror.text())
        self.name_edit.textChanged.connect(mirror.setText)


class DrilldownWidget(QtWidgets.QWidget):
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

        self.alarm_boxes = [
            AlarmBox(i, gen=gen)
            for i, gen in enumerate(self.parent().main_stack.graphs)
        ]
        for alarm_box in self.alarm_boxes:
            grid_layout.addWidget(alarm_box, *divmod(alarm_box.i, 2))
            alarm_box.clicked.connect(self.click_alarm)

    @Slot()
    def click_alarm(self):
        alarm_box = self.sender()
        self.parent().parent().drilldown_activate(alarm_box.i)

    def activate(self, i: int):
        "Call this to activate or switch drilldown screens!"

        for box in self.alarm_boxes:
            box.active = False
        self.alarm_boxes[i].active = True

        main_stack = self.parent().parent().main_stack

        name_btn = main_stack.graphs[i].title_widget.name_btn
        name_edit = main_stack.graphs[i].title_widget.name_edit

        self.patient.title.activate(name_btn.text(), name_edit)

        self.patient.gen = main_stack.graphs[i].gen
        self.patient.qTimer.start()

    def deactivate(self):
        self.patient.gen = None


class AlarmBox(QtWidgets.QPushButton):
    def __init__(self, i, *, gen):
        super().__init__(str(i + 1))
        self.i = i
        self.active = False

    @property
    def status(self) -> Status:
        return Status[self.property("alert_status")]

    @status.setter
    def status(self, value: Status):
        value_name = value.name + ("_ACTIVE" if self.active else "")
        if value_name != self.property("alert_status"):
            self.setProperty("alert_status", value_name)
            self.style().unpolish(self)
            self.style().polish(self)


class PatientDrilldownWidget(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.gen = None

        layout = HBoxLayout()
        self.setLayout(layout)

        left_layout = VBoxLayout()
        layout.addLayout(left_layout, 2)

        right_layout = VBoxLayout()
        layout.addLayout(right_layout, 1)

        self.title = PatientTitle()
        left_layout.addWidget(self.title)

        self.graphview = pg.GraphicsView(parent=self)
        graph_layout = pg.GraphicsLayout()
        self.graphview.setCentralWidget(graph_layout)
        left_layout.addWidget(self.graphview, 4)

        phaseview = pg.GraphicsView(parent=self)
        phase_layout = pg.GraphicsLayout()
        phaseview.setCentralWidget(phase_layout)
        right_layout.addWidget(phaseview)

        self.set_plot(graph_layout, phase_layout)

        left_layout.addWidget(QtWidgets.QLabel("Alarm settings"))
        self.alarm_cut_text = QtWidgets.QTextEdit()
        self.alarm_cut_text.setReadOnly(True)
        left_layout.addWidget(self.alarm_cut_text, 1)

        right_layout.addWidget(QtWidgets.QLabel("Values"))
        self.cumulative_text = QtWidgets.QTextEdit()
        self.cumulative_text.setReadOnly(True)
        right_layout.addWidget(self.cumulative_text)

        right_layout.addWidget(QtWidgets.QLabel("Active Alarms"))
        self.active_alarm_text = QtWidgets.QTextEdit()
        self.active_alarm_text.setReadOnly(True)
        right_layout.addWidget(self.active_alarm_text)

        right_layout.addWidget(QtWidgets.QLabel("Nurse log"))
        self.log_edit = QtWidgets.QTextEdit()
        right_layout.addWidget(self.log_edit)

        self.qTimer = QtCore.QTimer()
        self.qTimer.setSingleShot(True)
        self.qTimer.timeout.connect(self.update_plot)

    def set_plot(self, graph_layout, phase_layout):
        gis = GraphInfo()

        graphs = {}
        self.curves = {}

        for j, key in enumerate(gis.graph_labels):
            graphs[key] = graph_layout.addPlot(x=[], y=[], name=key.capitalize())
            graphs[key].invertX()
            graphs[key].setRange(xRange=(30, 0))
            if j != len(gis.graph_labels):
                graph_layout.nextRow()

            pen = pg.mkPen(color=gis.graph_pens[key], width=2)
            self.curves[key] = graphs[key].plot([], [], pen=pen)
            graphs[key].addLine(y=0)

        self.phase_graph = phase_layout.addPlot(x=[], y=[], name="Phase")

        self.phase = self.phase_graph.plot([], [], pen=pg.mkPen(color=(200, 200, 0)))
        self.phase_graph.setLabel("left", "Pressure", units="cm H2O")
        self.phase_graph.setLabel("bottom", "Volume", units="mL")

        graphs[gis.graph_labels[0]].setXLink(graphs[gis.graph_labels[1]])
        graphs[gis.graph_labels[1]].setXLink(graphs[gis.graph_labels[2]])

    @Slot()
    def update_plot(self):
        if self.isVisible() and self.gen is not None:
            gis = GraphInfo()
            tic = time.monotonic()

            with self.gen.lock:
                self.gen.get_data()
                full = self.gen.analyze_as_needed()

                # Fill in the data
                for key in gis.graph_labels:
                    self.curves[key].setData(self.gen.time, getattr(self.gen, key))

                self.phase.setData(self.gen.pressure, self.gen.flow)

                if True:
                    cumulative = "\n".join(
                        f"{k}: {v:g}" for k, v in self.gen.cumulative.items()
                    )
                    self.cumulative_text.setText(cumulative)

                    expand = lambda s: "".join(f"\n  {k}: {v:g}" for k, v in s.items())
                    active_alarms = "\n".join(
                        f"{k}: {expand(v)}" for k, v in self.gen.alarms.items()
                    )
                    self.active_alarm_text.setText(active_alarms)

            patient = self.parent()
            main_stack = patient.parent().parent().main_stack

            for alarm_box in patient.alarm_boxes:
                alarm_box.status = main_stack.graphs[alarm_box.i].gen.status

            toc = time.monotonic()
            t = toc - tic
            guess_each = int(t * 1000 * 1.1) + 30

            self.qTimer.start(max(guess_each, 100))
