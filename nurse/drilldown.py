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
from nurse.header import DrilldownHeaderWidget

from processor.generator import Status


class BoxHeader(QtWidgets.QLabel):
    pass


class DrilldownCumulative(QtWidgets.QLabel):
    pass


class DrilldownLimit(QtWidgets.QLabel):
    pass


class DrilldownLabel(QtWidgets.QLabel):
    pass


class DisplayBox(QtWidgets.QFrame):
    @property
    def status(self) -> Status:
        return Status[self.property("alert_status")]

    @status.setter
    def status(self, value: Status):
        if value.name != self.property("alert_status"):
            self.setProperty("alert_status", value.name)

            self.style().unpolish(self)
            self.style().polish(self)

            self.cumulative.style().unpolish(self.cumulative)
            self.cumulative.style().polish(self.cumulative)

    def __init__(self, *, key, label, fmt=""):
        super().__init__()
        self.key = key
        self.fmt = fmt
        layout = QtWidgets.QVBoxLayout(self)

        upper_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(upper_layout)

        upper_layout.addWidget(DrilldownLabel(label))
        upper_layout.addStretch()

        self.cumulative = DrilldownCumulative()
        upper_layout.addWidget(self.cumulative)

        lower_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(lower_layout)

        self.lower_limit = DrilldownLimit()
        lower_layout.addWidget(self.lower_limit)

        lower_layout.addStretch()

        self.upper_limit = DrilldownLimit()
        lower_layout.addWidget(self.upper_limit)

        self.update_cumulative()
        self.update_limits()

    def update_cumulative(self):
        gen = (
            self.parent().parent().gen
            if (self.parent() and self.parent().parent())
            else None
        )
        if gen is not None and self.key in gen.cumulative:
            self.cumulative.setText(format(gen.cumulative[self.key], self.fmt))
            if f"{self.key} Max" in gen.alarms or f"{self.key} Min" in gen.alarms:
                self.status = Status.ALERT
            else:
                self.status = Status.OK
        else:
            self.cumulative.setText("---")
            self.status = Status.DISCON

    def update_limits(self):
        min_key = f"{self.key} Min"
        max_key = f"{self.key} Max"

        gen = (
            self.parent().parent().gen
            if (self.parent() and self.parent().parent())
            else None
        )

        if gen is not None:
            if min_key in gen.rotary:
                self.lower_limit.setText(format(gen.rotary[min_key].value, self.fmt))

            if max_key in gen.rotary:
                self.upper_limit.setText(format(gen.rotary[max_key].value, self.fmt))


class AllDisplays(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.boxes = [
            DisplayBox(key="RR", label="RR", fmt=".0f"),
            DisplayBox(key="I:E time ratio", label="I:E", fmt=".2f"),
            DisplayBox(key="PIP", label="PIP", fmt=".0f"),
            DisplayBox(key="PEEP", label="PEEP", fmt=".0f"),
            DisplayBox(key="TVe", label="TVe", fmt=".0f"),
            DisplayBox(key="TVi", label="TVi", fmt=".0f"),
        ]

        layout = GridLayout(self)
        for n, box in enumerate(self.boxes):
            layout.addWidget(box, *divmod(n, 2))

    def update_cumulative(self):
        for box in self.boxes:
            box.update_cumulative()

    def update_limits(self):
        for box in self.boxes:
            box.update_limits()


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


class PatientTitle(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = HBoxLayout(self)

        self.name_lbl = QtWidgets.QLabel("X")
        layout.addWidget(self.name_lbl)

        self.name_edit = QtWidgets.QLineEdit()
        layout.addWidget(self.name_edit)

    def repolish(self):
        self.name_lbl.style().unpolish(self.name_lbl)
        self.name_edit.style().polish(self.name_edit)

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
            AlarmBox(i) for i in range(len(self.parent().main_stack.graphs))
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
    def __init__(self, i):
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
    @property
    def status(self):
        return Status[self.property("alert_status")]

    @status.setter
    def status(self, value: Status):
        if value.name != self.property("alert_status"):
            self.setProperty("alert_status", value.name)
            self.title.repolish()

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

        side_by_side_layout = HBoxLayout()
        right_layout.addLayout(side_by_side_layout, 3)

        nurse_layout = VBoxLayout()
        side_by_side_layout.addLayout(nurse_layout)

        displays_layout = VBoxLayout()
        side_by_side_layout.addLayout(displays_layout)

        self.displays = AllDisplays()
        displays_layout.addWidget(self.displays)
        displays_layout.addWidget(BoxHeader("Alarm log"))

        alarm_log = DisplayText()
        displays_layout.addWidget(alarm_log)

        nurse_layout.addWidget(BoxHeader("Nurse log"))
        self.log_edit = QtWidgets.QTextEdit()
        nurse_layout.addWidget(self.log_edit, 1)

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

                    self.status = self.gen.status
                    self.displays.update_cumulative()
                    self.displays.update_limits()

            patient = self.parent()
            main_stack = patient.parent().parent().main_stack

            for alarm_box in patient.alarm_boxes:
                alarm_box.status = main_stack.graphs[alarm_box.i].gen.status

            toc = time.monotonic()
            t += toc - tic
            guess_each = int(t * 1000 * 1.1) + 30

            self.qTimer.start(max(guess_each, 150))
