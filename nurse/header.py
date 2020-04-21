from nurse.qt import QtWidgets, QtGui, Qt, Slot, HBoxLayout
from nurse.common import GraphInfo


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
        layout.addWidget(logolabel, 0, Qt.AlignVCenter)
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
        super().__init__(key.capitalize() + "(" + gis.units[key] + ")")
        self.key = key

        self.setProperty("graph", key)
        self.clicked.connect(self.click_graph_info)

        self.limit = LimitDialog(key, parent=self)

    @Slot()
    def click_graph_info(self):
        b = self.limit.exec_()
        if b:
            for graph in self.parent().parent().parent().graphs:
                graph.graph[self.limit.key].setRange(
                    yRange=[
                        float(self.limit.lower.text()),
                        float(self.limit.upper.text()),
                    ]
                )


class LimitDialog(QtWidgets.QDialog):
    def __init__(self, name, parent):
        super().__init__()
        self.p = parent
        self.key = name
        self.setWindowTitle(f"Change {name} limits")
        self.setWindowModality(Qt.ApplicationModal)

        layout = QtWidgets.QVBoxLayout(self)

        form_layout = QtWidgets.QFormLayout()
        layout.addLayout(form_layout)

        self.upper = QtWidgets.QLineEdit()
        validator = QtGui.QDoubleValidator()
        self.upper.setValidator(validator)
        form_layout.addRow("Upper:", self.upper)

        self.lower = QtWidgets.QLineEdit()
        validator = QtGui.QDoubleValidator()
        self.lower.setValidator(validator)
        form_layout.addRow("Lower:", self.lower)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def exec_(self):
        graph = self.p.parent().parent().parent().graphs[0]
        l, u = graph.graph[self.key].viewRange()[1]
        self.upper.setText(format(u, "g"))
        self.lower.setText(format(l, "g"))
        return super().exec_()


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
        layout.addWidget(text, 1, Qt.AlignVCenter)

        for key in gis.graph_labels:
            name_btn = LimitButton(key)
            layout.addWidget(name_btn, 1, Qt.AlignVCenter)


class HeaderWidget(QtWidgets.QWidget):
    pass


class MainHeaderWidget(HeaderWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = HBoxLayout(self)

        princeton_logo = PrincetonLogoWidget()
        layout.addWidget(princeton_logo, 6)
        layout.addStretch()

        graph_info = GraphLabelWidget()
        layout.addWidget(graph_info, 6)

        nsf_logo = NSFLogoWidget()
        layout.addWidget(nsf_logo, 2)

        self.fs_exit = QtWidgets.QPushButton("X")
        self.fs_exit.setObjectName("exit_btn")
        self.fs_exit.setVisible(False)
        layout.addWidget(self.fs_exit)

        # dt_info = DateTimeWidget()
        # layout.addWidget(dt_info, 6) # Would need to be updated periodically
