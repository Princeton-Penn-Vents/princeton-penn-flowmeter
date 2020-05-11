from nurse.qt import QtWidgets, Qt, Slot
from processor.generator import Generator


class BasicTab(QtWidgets.QWidget):
    def __init__(self, gen: Generator):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)

        self.title = QtWidgets.QLineEdit()
        self.title.setPlaceholderText(gen.record.box_name)
        layout.addWidget(self.title)

        form_layout = QtWidgets.QFormLayout()
        layout.addLayout(form_layout)

        self.nid = QtWidgets.QLineEdit()
        form_layout.addRow("Short ID:", self.nid)

        view_layout = QtWidgets.QFormLayout()
        layout.addLayout(view_layout)

        form_layout.addRow("Box Name:", QtWidgets.QLabel(gen.record.box_name))


class DetailsTab(QtWidgets.QWidget):
    def __init__(self, gen: Generator):
        super().__init__()

        layout = QtWidgets.QFormLayout(self)

        layout.addRow("MAC Addr:", QtWidgets.QLabel(gen.record.mac))
        layout.addRow("Sensor:", QtWidgets.QLabel(format(gen.record.sid, "X")))
        layout.addRow(
            "IP Address:", QtWidgets.QLabel(getattr(gen, "address", "Simulation"))
        )


class GeneratorDialog(QtWidgets.QDialog):
    def __init__(self, gen: Generator):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        self.basic = BasicTab(gen)
        self.details = DetailsTab(gen)
        self.selection = QtWidgets.QTabWidget()
        self.selection.addTab(self.basic, "Basic")
        self.selection.addTab(self.details, "Details")
        layout.addWidget(self.selection)

        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.buttons.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.buttons.addButton("Disconnect", QtWidgets.QDialogButtonBox.DestructiveRole)
        layout.addWidget(self.buttons)

    def exec(self):
        return super().exec()
