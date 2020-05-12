from __future__ import annotations

import sys
from nurse.qt import QtWidgets, QtGui, QtCore, Qt, Slot, HBoxLayout


class HelpDialog(QtWidgets.QDialog):
    def __init__(self, default_tab: int = 0):
        super().__init__()
        self.setWindowTitle("Help")

        layout = QtWidgets.QVBoxLayout(self)

        tabs = QtWidgets.QTabWidget()
        layout.addWidget(tabs)

        main_help = QtWidgets.QLabel(
            r"""
        <p>At the top of the screen, you have the main menu bar. The three color coded graph labels after "Graph Settings" are clickable;
        clicking on them opens a limit selection dialog that can adjust the graph limits for all sensors. The next item on the menu is a "+" symbol,
        and clicking on that will open the add sensor dialog (advanced, usually not needed). Finally, you will see the "?" button that brought you here.</p>

        <p> The main screen has a grid of sensors. You can click the "i" to view information. You can click on the title to set it.
        You can click/tap on a sensor to enter the "drilldown"
        for that sensor. You can drag one sensor on another to swap their positions.</p>
        """
        )
        main_help.setWordWrap(True)
        tabs.addTab(main_help, "Main screen")

        drilldown_help = QtWidgets.QLabel(
            r"""
        <p> In the drilldown screen, there are a few new items in the top bar: </p>
        <ul>
        <li>Mode: can be set to Scroll or Overwrite</li>
        <li>Freeze: Will stop the screen from updating when selected</li>
        <li>Return to main window: Leave the drilldown</li>
        </ul>
        """
        )
        drilldown_help.setWordWrap(True)
        tabs.addTab(drilldown_help, "Drilldown")

        self.button = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        layout.addWidget(self.button)

        self.button.accepted.connect(self.close)

        tabs.setCurrentIndex(default_tab)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dialog = HelpDialog()
    dialog.show()
    sys.exit(app.exec_())
