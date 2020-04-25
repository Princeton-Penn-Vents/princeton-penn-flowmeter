import pyqtgraph as pg

import time

from nurse.qt import (
    QtCore,
    QtWidgets,
    Slot,
    HBoxLayout,
    VBoxLayout,
    GridLayout,
)

from nurse.common import GraphInfo
from nurse.header import HeaderWidget, PrincetonLogoWidget

from processor.generator import Status


class DisplayText(QtWidgets.QTextEdit):
    def __init__(self):
        super().__init__()

        self.setReadOnly(True)
        self._text = ""

    def update_if_needed(self, text, html=False):
        if self._text != text:
            self._text = text
            val = self.verticalScrollBar().value()
            if html:
                self.setHtml(text)
            else:
                self.setPlainText(text)
            self.verticalScrollBar().setValue(val)


class DrilldownHeaderWidget(HeaderWidget):
    def __init__(self):
        super().__init__()
        layout = HBoxLayout(self)

        layout.addWidget(PrincetonLogoWidget())
        layout.addStretch()
        layout.addWidget(QtWidgets.QPushButton("Mode: Scroll"))

        layout.addStretch()
        self.freeze_btn = QtWidgets.QCheckBox("Freeze")
        layout.addWidget(self.freeze_btn)
        layout.addStretch()
        self.return_btn = QtWidgets.QPushButton("Return to main view")
        self.return_btn.setObjectName("return_btn")
        layout.addWidget(self.return_btn)


class PatientTitle(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = HBoxLayout(self)

        self.name_lbl = QtWidgets.QLabel("X")
        layout.addWidget(self.name_lbl)

        self.name_edit = QtWidgets.QLineEdit()
        layout.addWidget(self.name_edit)

    def activate(self, number: str, mirror: QtWidgets.QLineEdit):
        self.name_edit.disconnect()
        self.name_lbl.setText(number)
        self.name_edit.setText(mirror.text())
        self.name_edit.textChanged.connect(mirror.setText)


class DrilldownWidget(QtWidgets.QWidget):
    def __init__(self, *, parent):
        super().__init__(parent=parent)

        layout = VBoxLayout(self)

        self.header = DrilldownHeaderWidget()
        self.return_btn = self.header.return_btn
        layout.addWidget(self.header)

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
        self.patient.update_plot(True)
        self.patient.qTimer.start(50)

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
        self.curves = {}
        self.gen = None

        layout = HBoxLayout(self)

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
        right_layout.addWidget(phaseview, 2)

        self.set_plot(graph_layout, phase_layout)

        left_layout.addWidget(QtWidgets.QLabel("Alarm settings"))
        self.alarm_cut_text = DisplayText()
        left_layout.addWidget(self.alarm_cut_text, 1)

        right_layout.addWidget(QtWidgets.QLabel("Values"))
        self.cumulative_text = DisplayText()
        right_layout.addWidget(self.cumulative_text, 1)

        right_layout.addWidget(QtWidgets.QLabel("Active Alarms"))
        self.active_alarm_text = DisplayText()
        right_layout.addWidget(self.active_alarm_text, 1)

        right_layout.addWidget(QtWidgets.QLabel("Nurse log"))
        self.log_edit = QtWidgets.QTextEdit()
        right_layout.addWidget(self.log_edit, 1)

        self.qTimer = QtCore.QTimer()
        self.qTimer.setSingleShot(True)
        self.qTimer.timeout.connect(self.update_plot)

    def set_plot(self, graph_layout, phase_layout):
        gis = GraphInfo()

        graphs = {}

        for j, key in enumerate(gis.graph_labels):
            graphs[key] = graph_layout.addPlot(x=[], y=[], name=key.capitalize())
            graphs[key].invertX()
            graphs[key].setRange(xRange=(30, 0))
            graphs[key].setLabel("left", gis.graph_names[key], gis.units[key])
            if j != len(gis.graph_labels):
                graph_layout.nextRow()

            pen = pg.mkPen(color=gis.graph_pens[key], width=2)
            self.curves[key] = graphs[key].plot([], [], pen=pen)
            graphs[key].addLine(y=0)

        graphs[key].setLabel("bottom", "Time", "s")

        graphs[gis.graph_labels[0]].setXLink(graphs[gis.graph_labels[1]])
        graphs[gis.graph_labels[1]].setXLink(graphs[gis.graph_labels[2]])

        # Phase plot
        self.phase_graph = phase_layout.addPlot(x=[], y=[], name="Phase")

        self.phase = self.phase_graph.plot([], [], pen=pg.mkPen(color=(200, 200, 0)))
        self.phase_graph.setLabel("left", "Volume", units="mL")
        self.phase_graph.setLabel("bottom", "Pressure", units="cm H2O")

    @Slot()
    def update_plot(self, first=False):
        if self.isVisible() and self.gen is not None:
            gis = GraphInfo()
            tic = time.monotonic()
            t = 0

            with self.gen.lock:

                if not first and self.parent().header.freeze_btn.checkState():
                    # Let's not retry too soon.
                    t += 100 / 1000
                else:
                    # Fill in the data
                    for key in gis.graph_labels:
                        self.curves[key].setData(self.gen.time, getattr(self.gen, key))

                    self.phase.setData(self.gen.pressure, self.gen.volume)

                    cumulative = "\n".join(
                        rf'<p><span style="font-weight:bold;">{k}</span>: {v:.2f}</p>'
                        for k, v in self.gen.cumulative.items()
                    )
                    self.cumulative_text.update_if_needed(cumulative, html=True)

                    expand = lambda s: "".join(
                        f"\n  {k}: {v}" for k, v in s.items()
                    )
                    active_alarms = "\n".join(
                        f"{k}: {expand(v)}" for k, v in self.gen.alarms.items()
                    )
                    self.active_alarm_text.update_if_needed(active_alarms)

                    rotary_text = "\n".join(
                        f"{v.name}: {v.value} {v.unit}"
                        for v in self.gen.rotary.values()
                    )
                    self.alarm_cut_text.update_if_needed(rotary_text)

            patient = self.parent()
            main_stack = patient.parent().parent().main_stack

            for alarm_box in patient.alarm_boxes:
                alarm_box.status = main_stack.graphs[alarm_box.i].gen.status

            toc = time.monotonic()
            t += toc - tic
            guess_each = int(t * 1000 * 1.1) + 30

            self.qTimer.start(max(guess_each, 150))
