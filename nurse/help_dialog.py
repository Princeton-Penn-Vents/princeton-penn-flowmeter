from __future__ import annotations

from nurse.qt import QtWidgets, QtGui, Qt, Slot, HBoxLayout
from nurse.common import GraphInfo
from datetime import datetime


class HelpDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(QtWidgets.QLabel("Help"))

        self.button = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        layout.addWidget(self.button)

        self.button.accepted.connect(self.close)
