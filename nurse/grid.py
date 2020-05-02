import pyqtgraph as pg

from datetime import datetime

from typing import Dict, Any

from nurse.qt import (
    QtWidgets,
    QtGui,
    Qt,
    Slot,
    HBoxLayout,
    VBoxLayout,
    FormLayout,
)

from nurse.common import GraphInfo

from processor.generator import Status, Generator
from processor.remote_generator import RemoteGenerator
from nurse.connection_dialog import ConnectionDialog

INFO_STRINGS = {
    "Avg Flow": ".0f",
    "Avg Pressure": ".0f",
    "RR": ".0f",  # (breaths/min)
    "TVe": ".0f",  # (mL)
    "PIP": ".0f",  # (cm H2O)
    "PEEP": ".0f",  # (cm H2O)
    "I:E time ratio": ".1f",
}


class NumberLabel(QtWidgets.QLabel):
    pass


class NumbersWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = FormLayout(self)

        self.val_widgets = {}

        for info in INFO_STRINGS:
            val_widget = NumberLabel("---")
            val_widget.setMinimumWidth(56)
            self.val_widgets[info] = val_widget
            layout.addRow(
                info.split()[-1][0] if info.startswith("Avg") else info.split()[0],
                self.val_widgets[info],
            )
            self.set_value(info, None)

    def set_value(self, info_str: str, value: float = None, ok: bool = True) -> None:
        val_widget = self.val_widgets[info_str]
        info_widget = self.layout().labelForField(val_widget)

        fmt = INFO_STRINGS[info_str]

        val_widget.setText("---" if value is None else f"{value:{fmt}}")

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
        self.i = i

        layout = HBoxLayout(self)

        # Temporary setting - i is the grid #, not Sensor ID
        self.name_btn = QtWidgets.QPushButton(f"{i+1}:")
        layout.addWidget(self.name_btn)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setText(f"Patient {i+1}")
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
        if value.name != self.property("alert_status"):
            self.setProperty("alert_status", value.name)
            self.title_widget.repolish()

            self.style().unpolish(self)
            self.style().polish(self)

    def __init__(self, *, i: int, gen: Generator):

        super().__init__()
        self.last_status_change = int(1000 * datetime.now().timestamp())
        self.gen: Generator = gen
        self.current_alarms: Dict[str, Any] = {}
        self.sensor_id = -1

        layout = HBoxLayout(self)

        layout_left = VBoxLayout()
        layout.addLayout(layout_left)

        self.title_widget = PatientTitleWidget(i=i)
        layout_left.addWidget(self.title_widget)

        self.graphview = GraphicsView(parent=self, i=i)
        graphlayout = pg.GraphicsLayout()
        graphlayout.setContentsMargins(0, 5, 0, 0)
        self.graphview.setCentralWidget(graphlayout)
        layout_left.addWidget(self.graphview)

        gis = GraphInfo()
        self.graph = {}
        for j, key in enumerate(gis.graph_labels):
            self.graph[key] = graphlayout.addPlot(x=None, y=None, name=key.capitalize())
            self.graph[key].setMouseEnabled(False, False)
            self.graph[key].invertX()
            if j != len(gis.graph_labels):
                graphlayout.nextRow()

        self.status = self.gen.status
        self.title_widget.name_btn.clicked.connect(self.click_number)

        self.values = NumbersWidget()
        layout.addWidget(self.values)

        self.curves: Dict[str, Any] = {}

    @Slot()
    def click_number(self):
        if isinstance(self.gen, RemoteGenerator):
            dialog = ConnectionDialog(self.parent().listener, self.gen)
            if dialog.exec_():
                self.gen.address = dialog.connection_address
        else:
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                "Local Generator",
                "Local generators cannot be changed, run without --sim next time.",
            )
            dialog.exec_()

    def set_plot(self):
        assert len(self.curves) == 0

        gis = GraphInfo()

        for i, (key, graph) in enumerate(self.graph.items()):
            pen = pg.mkPen(color=gis.graph_pens[key], width=2)

            self.curves[key] = graph.plot(x=None, y=None, pen=pen, autoDownsample=True)

            graph.setRange(xRange=(15, 0), yRange=gis.yLims[key])

            graph.getAxis("left").setStyle(
                tickTextOffset=2,
                textFillLimits=[(2, 1),],  ## Never have less than two ticks
            )

            if i != len(gis.graph_labels) - 1:
                graph.hideAxis("bottom")

            graph.addLine(y=0)

        self.graph[gis.graph_labels[0]].setXLink(self.graph[gis.graph_labels[1]])
        self.graph[gis.graph_labels[1]].setXLink(self.graph[gis.graph_labels[2]])

    def update_plot(self):
        gis = GraphInfo()

        with self.gen.lock:
            # Fill in the data
            for key in gis.graph_labels:
                if self.isVisible():
                    select = self.gen.time < 15 if len(self.gen.time) else slice(None)
                    self.curves[key].setData(
                        self.gen.time[select], getattr(self.gen, key)[select]
                    )
                else:
                    self.curves[key].setData(None, None)

            # Change of status requires a background color change
            self.status = self.gen.status

            sensor_id = int(self.gen.rotary["Sensor ID"].value)
            if self.sensor_id != sensor_id:
                self.title_widget.name_btn.setText(f"{sensor_id}:")
                self.sensor_id = sensor_id

            alarming_quanities = {key.rsplit(maxsplit=1)[0] for key in self.gen.alarms}

            for key in self.values:
                if key == "Avg Flow":
                    value = self.gen.average_flow[self.gen.rotary["AvgWindow"].value]
                elif key == "Avg Pressure":
                    value = self.gen.average_pressure[
                        self.gen.rotary["AvgWindow"].value
                    ]
                else:
                    value = self.gen.cumulative.get(key)

                self.values.set_value(
                    key, value=value, ok=key not in alarming_quanities,
                )
