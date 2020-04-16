from nurse.qt import QtWidgets, QtGui, Qt, Slot, HBoxLayout
from nurse.common import GraphInfo


class PrincetonLogoWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = HBoxLayout()
        self.setLayout(layout)

        logo = QtGui.QPixmap("images/PUsig2-158C-shield.png").scaledToWidth(18)
        logolabel = QtWidgets.QLabel()
        logolabel.setPixmap(logo)

        text = QtWidgets.QLabel("Princeton Open Vent Monitor")
        text.setMinimumWidth(90)
        text.setAlignment(Qt.AlignLeft)
        layout.addWidget(logolabel, 0, Qt.AlignVCenter)
        layout.addWidget(text, 0, Qt.AlignVCenter)
        layout.addStretch()
        layout.setSpacing(0)


class NSFLogoWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = HBoxLayout()
        self.setLayout(layout)

        logo = QtGui.QPixmap("images/nsf-logo-100.png").scaledToWidth(25)
        logolabel = QtWidgets.QLabel()
        logolabel.setPixmap(logo)
        layout.addWidget(logolabel, 0, Qt.AlignVCenter)
        layout.setAlignment(Qt.AlignRight)


class DateTimeWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = HBoxLayout()
        self.setLayout(layout)

        now = datetime.now()
        nowstring = now.strftime("%d %b %Y %H:%M:%S")
        text = QtWidgets.QLabel(nowstring)
        text.setAlignment(Qt.AlignLeft)
        layout.addWidget(text, 0, Qt.AlignVCenter)
        layout.addStretch()


class GraphLabelWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = HBoxLayout()
        self.setLayout(layout)

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
        self.buttons = {}

        for key in gis.graph_labels:
            name_btn = QtWidgets.QPushButton(
                key.capitalize() + "(" + gis.units[key] + ")"
            )
            name_btn.setProperty("graph", key)
            self.buttons[key] = name_btn
            layout.addWidget(name_btn, 1, Qt.AlignVCenter)
            name_btn.clicked.connect(self.click_graph_info)

    @Slot()
    def click_graph_info(self):
        # ok - this needs to get generalized and extended
        number, ok = QtWidgets.QInputDialog.getDouble(
            self, "Adjust plots", "Min Y axis", 10, 0, 100
        )
        if ok:
            try:
                print("Found number", number, ok)
            except ValueError:
                return


class HeaderWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = HBoxLayout()
        self.setLayout(layout)

        princeton_logo = PrincetonLogoWidget()
        graph_info = GraphLabelWidget()
        nsf_logo = NSFLogoWidget()
        # dt_info = DateTimeWidget()
        layout.addWidget(princeton_logo, 6)
        layout.addWidget(graph_info, 6)
        # layout.addWidget(dt_info, 6) # Would need to be updated periodically
        layout.addWidget(nsf_logo, 2)
