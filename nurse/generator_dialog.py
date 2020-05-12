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
        self.discon = self.buttons.addButton(
            "Disconnect", QtWidgets.QDialogButtonBox.DestructiveRole
        )
        self.discon.setEnabled(False)
        self.discon.setToolTip("You can only disconnect an unplugged sensor")
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def exec(self) -> int:
        res = super().exec()
        print(f"Accepted: {res}")
        return res
