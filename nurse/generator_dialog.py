from nurse.qt import QtWidgets, Slot
from processor.generator import Generator, Status
from processor.local_generator import LocalGenerator


class BasicTab(QtWidgets.QWidget):
    def __init__(self, gen: Generator):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(
            QtWidgets.QLabel(
                "Please make sure a title is set to make box identification easier.\n"
                "The first few characters will be shown in the drilldown alarm screen."
            )
        )

        form_layout = QtWidgets.QFormLayout()
        layout.addLayout(form_layout)

        self.title = QtWidgets.QLineEdit()
        self.title.setPlaceholderText("Please enter title")
        self.title.setText(gen.record.title)

        form_layout.addRow("Title:", self.title)
        form_layout.addRow("Box Name:", QtWidgets.QLabel(gen.record.box_name))


class DetailsTab(QtWidgets.QWidget):
    def __init__(self, gen: Generator):
        super().__init__()

        layout = QtWidgets.QFormLayout(self)

        layout.addRow("MAC Addr:", QtWidgets.QLabel(gen.record.mac))
        layout.addRow("Sensor:", QtWidgets.QLabel(format(gen.record.sid, "016X")))
        layout.addRow(
            "IP Address:", QtWidgets.QLabel(getattr(gen, "address", "Simulation"))
        )


class GeneratorDialog(QtWidgets.QDialog):
    def __init__(
        self, parent: QtWidgets.QWidget, gen: Generator, *, grid: bool = False
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Info for {gen.record.box_name}")

        self.gen = gen
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

        if grid:
            self.discon = self.buttons.addButton(
                "Disconnect", QtWidgets.QDialogButtonBox.DestructiveRole
            )
            self.discon.setEnabled(
                self.gen.status == Status.DISCON or isinstance(self.gen, LocalGenerator)
            )
            self.discon.setToolTip("You can only disconnect an unplugged sensor")
            self.buttons.destroyed.connect(self.disconnect_sensor)

        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    @Slot()
    def disconnect_sensor(self) -> None:
        self.discon = True
        self.reject()

    @Slot()
    def accept(self) -> None:
        self.gen.record.title = self.basic.title.text()
        super().accept()
