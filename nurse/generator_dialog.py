from nurse.qt import QtWidgets, Qt, Slot


class GeneratorDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)

    def exec(self):
        return super().exec()
