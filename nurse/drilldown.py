from __future__ import annotations

import pyqtgraph as pg

from typing import Optional, Dict, List

import numpy as np

from nurse.qt import (
    QtCore,
    QtWidgets,
    Qt,
    QtGui,
    Slot,
    HBoxLayout,
    VBoxLayout,
    GridLayout,
    BoxName,
)

from nurse.common import GraphInfo
from nurse.header import DrilldownHeaderWidget
from nurse.gen_record_gui import GenRecordGUI
from processor.generator import Status, Generator
from nurse.generator_dialog import GeneratorDialog


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

    def __init__(self, *, key: str, label: str, fmt: str = ""):
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

        if self.key.startswith("Avg "):
            self.avg_time = DrilldownLimit()
            lower_layout.addWidget(self.avg_time)
            lower_layout.addStretch()

        self.upper_limit = DrilldownLimit()
        lower_layout.addWidget(self.upper_limit)

        self.update_cumulative()
        self.update_limits()

    def update_cumulative(self):
        gen: Optional[Generator] = (
            self.parent().parent().gen
            if (self.parent() and self.parent().parent())
            else None
        )

        if gen is None:
            value = None
        elif self.key == "Avg Flow":
            avg_window = gen.rotary["AvgWindow"].value
            value = gen.average_flow[avg_window]
        elif self.key == "Avg Pressure":
            avg_window = gen.rotary["AvgWindow"].value
            value = gen.average_pressure[avg_window]
        else:
            value = gen.cumulative.get(self.key)

        if value is not None:
            self.cumulative.setText(format(value, self.fmt))
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

            if hasattr(self, "avg_time"):
                self.avg_time.setText(f"({gen.rotary['AvgWindow']})")


class AllDisplays(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.boxes = [
            DisplayBox(key="Avg Flow", label="Flow", fmt=".0f"),
            DisplayBox(key="Avg Pressure", label="P", fmt=".0f"),
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

        self.name_lbl = QtWidgets.QPushButton("i")
        self.name_lbl.clicked.connect(self.click_number)
        layout.addWidget(self.name_lbl)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Please enter title")
        layout.addWidget(self.name_edit)

        self.name_edit.editingFinished.connect(self.update_title)

    @property
    def record(self) -> GenRecordGUI:
        return self.parent().gen.record

    def repolish(self) -> None:
        self.name_lbl.style().unpolish(self.name_lbl)
        self.name_edit.style().polish(self.name_edit)

    def activate(self) -> None:
        self.name_edit.setText(self.record.title)
        self.record.master_signal.title_changed.connect(self.external_update_title)

    def deactivate(self) -> None:
        if self.parent().gen is not None:
            self.record.master_signal.title_changed.disconnect(
                self.external_update_title
            )

    @Slot()
    def external_update_title(self) -> None:
        self.name_edit.setText(self.record.title)

    @Slot()
    def update_title(self) -> None:
        self.record.title = self.name_edit.text()

    @Slot()
    def click_number(self) -> None:
        dialog = GeneratorDialog(self, self.parent().gen)
        dialog.open()


class DrilldownWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)

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

        self.alarms_layout = VBoxLayout()
        side_layout.addLayout(self.alarms_layout)
        side_layout.addStretch()

        self.alarm_boxes: List[AlarmBox] = []

    def add_alarm_box(self, gen: Generator, i: int):
        alarm_box = AlarmBox(gen, i)
        self.alarm_boxes.append(alarm_box)
        self.alarms_layout.addWidget(alarm_box)
        alarm_box.clicked.connect(self.click_alarm)

    @Slot()
    def click_alarm(self):
        alarm_box: AlarmBox = self.sender()
        self.parent().parent().drilldown_activate(alarm_box.i)

    def activate(self, i: int):
        if self.patient.gen is not None:
            self.deactivate()

        "Call this to activate or switch drilldown screens!"

        for n, box in enumerate(self.alarm_boxes):
            box.active = i == n
            box.update_gen()

        main_stack = self.parent().parent().main_stack

        record: GenRecordGUI
        if self.patient.gen is not None:
            record = self.patient.gen.record
            record.master_signal.mac_changed.disconnect(
                self.patient.external_update_boxname
            )
            record.master_signal.sid_changed.disconnect(
                self.patient.external_update_sid
            )

        self.patient.gen = main_stack.graphs[i].gen
        self.patient.title.activate()

        record = self.patient.gen.record
        record.master_signal.mac_changed.connect(self.patient.external_update_boxname)
        record.master_signal.sid_changed.connect(self.patient.external_update_sid)
        record.master_signal.notes_changed.connect(self.patient.external_update_notes)

        self.patient.external_update_boxname()
        self.patient.external_update_sid()
        self.patient.external_update_notes()

        self.patient.update_plot(True)

    def deactivate(self) -> None:
        record: GenRecordGUI
        record = self.patient.gen.record

        record.master_signal.mac_changed.disconnect(
            self.patient.external_update_boxname
        )
        record.master_signal.sid_changed.disconnect(self.patient.external_update_sid)

        record.master_signal.notes_changed.disconnect(
            self.patient.external_update_notes
        )

        self.patient.title.deactivate()
        self.patient.gen = None
        self.patient.qTimer.stop()


class AlarmBox(QtWidgets.QPushButton):
    def __init__(self, gen: Generator, i: int):
        super().__init__()
        self.gen: Generator = gen
        record: GenRecordGUI
        record = self.gen.record  # type: ignore
        record.master_signal.title_changed.connect(self.update_gen)
        self.active = False
        self.i = i

        self.stack = QtWidgets.QStackedLayout()
        self.setLayout(self.stack)

        boxname_container = QtWidgets.QWidget()
        boxname_layout = VBoxLayout(boxname_container)
        self.stack.addWidget(boxname_container)
        self.upper = BoxName("Box name")
        self.lower = BoxName("Unknown")
        boxname_layout.addWidget(self.upper, 0, Qt.AlignHCenter)
        boxname_layout.addWidget(self.lower, 0, Qt.AlignHCenter)

        title_container = QtWidgets.QWidget()
        title_layout = VBoxLayout(title_container)
        self.title = QtWidgets.QLabel("")
        title_layout.addWidget(self.title, 0, Qt.AlignHCenter)
        self.stack.addWidget(title_container)

        self.update_gen()

    @Slot()
    def update_gen(self):
        if self.gen.record.title:
            self.title.setText(self.gen.record.title)
            self.stack.setCurrentIndex(1)
        else:
            upper, lower = self.gen.record.stacked_name.split("\n")
            self.upper.setText(upper)
            self.lower.setText(lower)
            self.stack.setCurrentIndex(0)

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


class LogTextEdit(QtWidgets.QPlainTextEdit):
    def __init__(self):
        super().__init__()

        self.text_changed = False
        self.textChanged.connect(self.update_notes)

    @Slot()
    def update_notes(self):
        self.text_changed = True

    @property
    def record(self) -> GenRecordGUI:
        return self.parent().gen.record

    def focusOutEvent(self, e: QtGui.QFocusEvent) -> None:
        if self.text_changed:
            self.record.notes = self.toPlainText()
        self.text_changed = False


class PatientDrilldownWidget(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.curves: Dict[str, pg.PlotCurveItem] = {}
        self.curves2: Dict[str, pg.PlotCurveItem] = {}
        self.upper = {}
        self.lower = {}
        self.current = {}
        self.gen: Optional[Generator] = None

        layout = HBoxLayout(self)

        left_layout = VBoxLayout()
        layout.addLayout(left_layout, 2)

        right_layout = VBoxLayout()
        layout.addLayout(right_layout, 1)

        self.title = PatientTitle()
        left_layout.addWidget(self.title)

        warning_layout = QtWidgets.QHBoxLayout()
        left_layout.addLayout(warning_layout)

        warning_layout.addStretch()

        warning_layout.addWidget(QtWidgets.QLabel("Box name: "))
        self.box_name = BoxName("???")
        warning_layout.addWidget(self.box_name)

        warning_layout.addStretch()

        self.sensor_id = QtWidgets.QLabel("Sensor ID: ???")
        warning_layout.addWidget(self.sensor_id)

        warning_layout.addStretch()

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

        displays_layout = VBoxLayout()
        side_by_side_layout.addLayout(displays_layout)

        nurse_layout = VBoxLayout()
        side_by_side_layout.addLayout(nurse_layout)

        self.displays = AllDisplays()
        displays_layout.addWidget(self.displays)

        self.last_ts = QtWidgets.QLabel("Last updated: ---")
        self.last_ts.setObjectName("LastTS")
        displays_layout.addWidget(self.last_ts)

        button_box = QtWidgets.QWidget()
        button_box.setObjectName("DrilldownExtras")
        buttons_layout = QtWidgets.QHBoxLayout(button_box)
        displays_layout.addWidget(button_box)

        all_alarms = QtWidgets.QPushButton("Alarms")
        all_cumulative = QtWidgets.QPushButton("Quantities")
        all_rotary = QtWidgets.QPushButton("Settings")

        all_alarms.clicked.connect(self.display_alarms)
        all_cumulative.clicked.connect(self.display_cumulative)
        all_rotary.clicked.connect(self.display_rotary)

        buttons_layout.addWidget(all_alarms, 1)
        buttons_layout.addWidget(all_cumulative, 1)
        buttons_layout.addWidget(all_rotary, 1)

        lim_help = QtWidgets.QLabel("All alarm limits are set on the device")
        displays_layout.addWidget(lim_help)

        displays_layout.addStretch()

        nurse_layout.addWidget(BoxHeader("Notes:"))
        self.log_edit = LogTextEdit()
        nurse_layout.addWidget(self.log_edit, 1)

        self.qTimer = QtCore.QTimer()
        self.qTimer.setSingleShot(True)
        self.qTimer.timeout.connect(self.update_plot)

    @property
    def status(self):
        return Status[self.property("alert_status")]

    @status.setter
    def status(self, value: Status):
        if value.name != self.property("alert_status"):
            self.setProperty("alert_status", value.name)
            self.title.repolish()

    @Slot()
    def display_cumulative(self):
        if self.gen is not None:
            cumulative = "\n".join(
                rf"<p>{k}: {v:.2f}</p>" for k, v in self.gen.cumulative.items()
            )
        else:
            cumulative = "Disconnected"
        if not cumulative:
            cumulative = "No computed values yet"

        box = QtWidgets.QMessageBox()
        box.setWindowTitle("Computed values")
        box.setTextFormat(Qt.RichText)
        box.setText(cumulative)
        box.exec()

    @Slot()
    def display_alarms(self):
        expand = lambda s: "".join(f"<br>  {k}: {v}" for k, v in s.items())
        active_alarms = "\n".join(
            rf"<p>{k}: {expand(v)}</p>" for k, v in self.gen.alarms.items()
        )

        if not active_alarms:
            active_alarms = "No alarms currently."

        box = QtWidgets.QMessageBox()
        box.setWindowTitle("Active alarms")
        box.setTextFormat(Qt.RichText)
        box.setText(active_alarms)
        box.exec()

    @Slot()
    def display_rotary(self):
        rotary_text = "\n".join(
            rf"<p>{v.name}: {v.value} {v.unit}</p>" for v in self.gen.rotary.values()
        )

        box = QtWidgets.QMessageBox()
        box.setWindowTitle("Currently set alarm limits")
        box.setTextFormat(Qt.RichText)
        box.setText(rotary_text)
        box.exec()

    @Slot()
    def external_update_boxname(self):
        text = self.gen.record.box_name
        if self.box_name.text() != text:
            self.box_name.setText(text)

    @Slot()
    def external_update_sid(self):
        text = f"Sensor ID: {self.gen.record.sid:016X}"
        if self.sensor_id.text() != text:
            self.sensor_id.setText(text)

    @Slot()
    def external_update_notes(self):
        text = self.gen.record.notes
        self.log_edit.setPlainText(text)

    def set_plot(self, graph_layout, phase_layout):
        gis = GraphInfo()

        graphs = {}

        limit_pen = pg.mkPen(color=(170, 30, 30), width=3, style=QtCore.Qt.DashLine)
        current_pen = pg.mkPen(color=(50, 50, 180), width=3, style=QtCore.Qt.DotLine)

        for j, key in enumerate(gis.graph_labels):
            graphs[key] = graph_layout.addPlot(
                x=None,
                y=None,
                name=key.capitalize(),
                autoDownsample=True,
                clipToView=True,
            )
            graphs[key].invertX()
            graphs[key].setRange(xRange=(30, 0))
            graphs[key].setLabel("left", gis.graph_names[key], gis.units[key])
            if j != len(gis.graph_labels):
                graph_layout.nextRow()

            graphs[key].addItem(pg.PlotDataItem([0, 30], [0, 0]))

            self.upper[key] = pg.PlotDataItem(x=None, y=None, pen=limit_pen)
            graphs[key].addItem(self.upper[key])
            self.lower[key] = pg.PlotDataItem(x=None, y=None, pen=limit_pen)
            graphs[key].addItem(self.lower[key])
            self.current[key] = pg.PlotDataItem(x=None, y=None, pen=current_pen)
            graphs[key].addItem(self.current[key])

            pen = pg.mkPen(color=gis.graph_pens[key], width=2)
            self.curves[key] = graphs[key].plot(x=None, y=None, pen=pen)
            self.curves2[key] = graphs[key].plot(x=None, y=None, pen=pen)

        graphs[key].setLabel("bottom", "Time", "s")

        graphs[gis.graph_labels[0]].setXLink(graphs[gis.graph_labels[1]])
        graphs[gis.graph_labels[1]].setXLink(graphs[gis.graph_labels[2]])

        # Phase plot
        self.phase_graph = phase_layout.addPlot(x=None, y=None, name="Phase")
        self.phase = self.phase_graph.plot(
            x=None, y=None, pen=pg.mkPen(color=(200, 200, 0))
        )
        self.phase_graph.setLabel("left", "Volume", units="mL")
        self.phase_graph.setLabel("bottom", "Pressure", units="cm H2O")

    @Slot()
    def update_plot(self, first: bool = False):
        if self.isVisible() and self.gen is not None:
            gis = GraphInfo()
            scroll = self.parent().header.mode_scroll

            with self.gen.lock:
                if first or not self.parent().header.freeze_btn.checkState():
                    time_avg = self.gen.rotary["AvgWindow"].value

                    for key in gis.graph_labels:
                        if scroll:
                            self.curves[key].setData(
                                self.gen.time, getattr(self.gen, key)
                            )
                            x, _y = self.curves2[key].getData()
                            if x is not None and len(x) > 0:
                                self.curves2[key].setData(
                                    x=np.array([], dtype=float),
                                    y=np.array([], dtype=float),
                                )

                        else:
                            last = self.gen.realtime[-1]
                            breakpt = np.searchsorted(
                                self.gen.realtime, last - last % 30
                            )
                            gap = 25

                            self.curves[key].setData(
                                30 - (self.gen.realtime[breakpt:] % 30),
                                getattr(self.gen, key)[breakpt:],
                            )
                            self.curves2[key].setData(
                                30 - (self.gen.realtime[gap:breakpt] % 30),
                                getattr(self.gen, key)[gap:breakpt],
                            )

                        val_key = f"Avg {key.capitalize()}"
                        min_key = f"{val_key} Min"
                        max_key = f"{val_key} Max"
                        if min_key in self.gen.rotary:
                            self.lower[key].setData(
                                [0, 30], [self.gen.rotary[min_key].value] * 2
                            )
                        if max_key in self.gen.rotary:
                            self.upper[key].setData(
                                [0, 30], [self.gen.rotary[max_key].value] * 2
                            )

                        if val_key == "Avg Flow":
                            self.current[key].setData(
                                [0, time_avg], [self.gen.average_flow[time_avg]] * 2
                            )
                        elif val_key == "Avg Pressure":
                            self.current[key].setData(
                                [0, time_avg], [self.gen.average_pressure[time_avg]] * 2
                            )

                    self.phase.setData(self.gen.pressure, self.gen.volume)

                    self.status = self.gen.status
                    self.displays.update_cumulative()
                    self.displays.update_limits()

                    time_str = (
                        "now" if self.gen.tardy < 1 else f"{self.gen.tardy:.0f}s ago"
                    )
                    date_str = (
                        "---"
                        if self.gen.last_update is None
                        else format(self.gen.last_update, "%m-%d-%Y %H:%M:%S")
                    )

                    for breath in reversed(self.gen.breaths):
                        if "full timestamp" in breath:
                            time_since = (
                                self.gen.realtime[-1] - breath["full timestamp"]
                            ) + self.gen.tardy
                            breath_str = f"Most recent breath: {time_since:.0f} s ago"
                            break
                    else:
                        breath_str = "No detected breaths yet"
                    self.last_ts.setText(
                        f"Updated: {time_str} @ {date_str}\n{breath_str}"
                    )

            patient = self.parent()
            main_stack = patient.parent().parent().main_stack

            for alarm_box, graph in zip(patient.alarm_boxes, main_stack.graphs):
                alarm_box.status = graph.gen.status

        self.qTimer.start(50)
