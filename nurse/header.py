from nurse.qt import QtWidgets, QtGui, Qt, Slot, HBoxLayout
from nurse.common import GraphInfo, dialog_style_path
from datetime import datetime


class PrincetonLogoWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = HBoxLayout(self)

        logo = QtGui.QPixmap("images/PUsig2-158C-shield.png").scaledToWidth(18)
        logolabel = QtWidgets.QLabel()
        logolabel.setPixmap(logo)

        text = QtWidgets.QLabel("Princeton Open Vent Monitor")
        text.setMinimumWidth(90)
        text.setAlignment(Qt.AlignLeft)
        layout.addWidget(logolabel, 0, Qt.AlignVCenter)
        layout.addWidget(text, 0, Qt.AlignVCenter)
        layout.setSpacing(0)


class NSFLogoWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = HBoxLayout(self)

        logo = QtGui.QPixmap("images/nsf-logo-100.png").scaledToWidth(25)
        logolabel = QtWidgets.QLabel()
        logolabel.setPixmap(logo)
        layout.addWidget(logolabel)
        layout.setAlignment(Qt.AlignRight)


class DateTimeWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = HBoxLayout(self)

        now = datetime.now()
        nowstring = now.strftime("%d %b %Y %H:%M:%S")
        text = QtWidgets.QLabel(nowstring)
        text.setAlignment(Qt.AlignLeft)
        layout.addWidget(text, 0, Qt.AlignVCenter)
        layout.addStretch()


class LimitButton(QtWidgets.QPushButton):
    def __init__(self, key):
        gis = GraphInfo()
        super().__init__(f"{key.capitalize()}({gis.units[key]})")
        self.key = key

        self.setProperty("graph", key)
        self.clicked.connect(self.click_graph_info)

        self.limit = LimitDialog(key, parent=self)

    @Slot()
    def click_graph_info(self):
        b = self.limit.exec()
        if b:
            for graph in self.parent().parent().parent().graphs:
                graph.graph[self.limit.key].setRange(
                    yRange=[self.limit.lower.value(), self.limit.upper.value(),]
                )
        else:
            for graph in self.parent().parent().parent().graphs:
                graph.graph[self.limit.key].setRange(
                    yRange=[self.limit.orig_lower, self.limit.orig_upper,]
                )


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


class GraphLabelWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = HBoxLayout(self)

        gis = GraphInfo()

        alpha = 140
        values = {}
        for key in gis.graph_pen_qcol:
            pen = gis.graph_pen_qcol[key]
            values[key] = "{r}, {g}, {b}, {a}".format(
                r=pen.red(), g=pen.green(), b=pen.blue(), a=alpha
            )

        text = QtWidgets.QLabel("Graph settings")
        text.setAlignment(Qt.AlignLeft)
        layout.addWidget(text, 0, Qt.AlignVCenter)

        for key in gis.graph_labels:
            name_btn = LimitButton(key)
            layout.addWidget(name_btn, 0, Qt.AlignVCenter)


class HeaderWidget(QtWidgets.QWidget):
    pass


class MainHeaderWidget(HeaderWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = HBoxLayout(self)

        princeton_logo = PrincetonLogoWidget()
        layout.addWidget(princeton_logo)

        layout.addStretch()

        graph_info = GraphLabelWidget()
        layout.addWidget(graph_info)

        self.add_btn = QtWidgets.QPushButton("+")
        layout.addWidget(self.add_btn)

        nsf_logo = NSFLogoWidget()
        layout.addWidget(nsf_logo)

        self.fs_exit = QtWidgets.QPushButton("X")
        self.fs_exit.setObjectName("exit_btn")
        self.fs_exit.setVisible(False)
        layout.addWidget(self.fs_exit)

        # dt_info = DateTimeWidget()
        # layout.addWidget(dt_info, 6) # Would need to be updated periodically


class DrilldownHeaderWidget(HeaderWidget):
    def __init__(self):
        super().__init__()
        layout = HBoxLayout(self)

        layout.addWidget(PrincetonLogoWidget())
        layout.addStretch()

        self.mode_btn = QtWidgets.QPushButton("Mode: Scroll")
        self.mode_btn.setObjectName("mode_btn")
        self.mode_btn.clicked.connect(self.mode_btn_callback)
        layout.addWidget(self.mode_btn)

        self.freeze_btn = QtWidgets.QCheckBox("Freeze")
        layout.addWidget(self.freeze_btn)

        self.return_btn = QtWidgets.QPushButton("Return to main view")
        self.return_btn.setObjectName("return_btn")
        layout.addWidget(self.return_btn, 0, Qt.AlignVCenter)

        nsf_logo = NSFLogoWidget()
        layout.addWidget(nsf_logo)

    @property
    def mode_scroll(self):
        return self.mode_btn.text() == "Mode: Scroll"

    @Slot()
    def mode_btn_callback(self):
        if self.mode_scroll:
            self.mode_btn.setText("Mode: Overwrite")
        else:
            self.mode_btn.setText("Mode: Scroll")
