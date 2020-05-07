from nurse.qt import QtWidgets, Qt, Slot
from nurse.common import GraphInfo, dialog_style_path


class LimitSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, key, is_upper):
        super().__init__()
        self.key = key
        self.is_upper = is_upper
        gis = GraphInfo()

        self.setMaximum(gis.yMax[self.key])
        self.setMinimum(gis.yMin[self.key])
        self.setSingleStep(gis.yStep[self.key])
        self.setSuffix(" " + gis.units[self.key])


class LimitDialog(QtWidgets.QDialog):
    def __init__(self, name, parent):
        super().__init__()
        gis = GraphInfo()
        self.p = parent
        self.key = name
        self.setWindowTitle(f"Change {name} limits")
        self.setWindowModality(Qt.ApplicationModal)
        self.orig_lower: float = gis.yLims[self.key][0]
        self.orig_upper: float = gis.yLims[self.key][1]

        layout = QtWidgets.QVBoxLayout(self)

        form_layout = QtWidgets.QFormLayout()
        layout.addLayout(form_layout)

        self.upper = LimitSpinBox(self.key, True)
        form_layout.addRow("Upper:", self.upper)
        self.upper.valueChanged.connect(self.change_value)

        self.lower = LimitSpinBox(self.key, False)
        form_layout.addRow("Lower:", self.lower)
        self.lower.valueChanged.connect(self.change_value)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        with open(dialog_style_path) as f:
            self.setStyleSheet(f.read())

    def exec(self):
        graphs = self.p.parent().parent().parent().graphs
        if not graphs:
            return QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                "No sensors connected",
                "No sensors are connected, use the + button on the top right or plug in a sensor.",
            ).exec()

        graph = graphs[0]
        self.orig_lower, self.orig_upper = graph.graph[self.key].viewRange()[1]
        self.lower.setValue(self.orig_lower)
        self.upper.setValue(self.orig_upper)
        return super().exec()

    @Slot()
    def change_value(self):
        for graph in self.p.parent().parent().parent().graphs:
            graph.graph[self.key].setRange(
                yRange=[self.lower.value(), self.upper.value(),]
            )
