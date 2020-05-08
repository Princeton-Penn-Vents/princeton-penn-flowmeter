from __future__ import annotations

from urllib.parse import urlparse
from processor.listener import FindBroadcasts, Detector
from typing import List

from nurse.qt import (
    QtWidgets,
    QtGui,
    Qt,
)


class ManualTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QFormLayout(self)

        self.ip_address = QtWidgets.QLineEdit()
        layout.addRow("IP Address:", self.ip_address)

        self.port = QtWidgets.QLineEdit()
        validator = QtGui.QIntValidator()
        self.port.setValidator(validator)
        layout.addRow("Port:", self.port)


class DetectedTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QFormLayout(self)

        self.detected = QtWidgets.QComboBox()
        layout.addRow("Detected:", self.detected)

        self.detected.setMinimumWidth(180)


class TabbedConnection(QtWidgets.QTabWidget):
    def __init__(self):
        super().__init__()

        self.detected_tab = DetectedTab()
        self.addTab(self.detected_tab, "Detected")

        self.manual_tab = ManualTab()
        self.addTab(self.manual_tab, "Manual IP")


class ConnectionDialog(QtWidgets.QDialog):
    def __init__(self, listener: FindBroadcasts, i: int, address: str):
        super().__init__()

        self.i = i
        self.listener = listener
        self.address = address
        self.items: List[Detector] = []

        self.setWindowModality(Qt.ApplicationModal)

        layout = QtWidgets.QVBoxLayout(self)

        self.tabbed = TabbedConnection()
        layout.addWidget(self.tabbed)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.ok, cancel = buttons.buttons()

        layout.addWidget(buttons)

    def exec(self):
        self.setWindowTitle(f"Patient box {self.i} connection")

        parsed = urlparse(self.address)
        self.tabbed.manual_tab.ip_address.setText(parsed.hostname)
        self.tabbed.manual_tab.port.setText(str(parsed.port))

        self.items = list(self.listener.detected)
        items = [str(d) for d in self.items]
        self.tabbed.detected_tab.detected.addItems(items)

        if not items:
            self.tabbed.setCurrentIndex(1)
            self.tabbed.setTabEnabled(0, False)

        return super().exec()

    def connection_address(self) -> str:
        if self.tabbed.currentIndex() == 0:
            return self.items[self.tabbed.detected_tab.detected.currentIndex()].url
        else:
            port = int(self.tabbed.manual_tab.port.text())
            ip_address = self.tabbed.manual_tab.ip_address.text()
            return f"tcp://{ip_address}:{port}"
