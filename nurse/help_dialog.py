from __future__ import annotations

import sys
from nurse.qt import QtWidgets, PopdownTitle, DraggableMixin
from processor.version import get_version
from string import Template
from nurse.common import style_path, GraphInfo


class HelpDialog(QtWidgets.QDialog, DraggableMixin):
    def __init__(self, parent: QtWidgets.QWidget = None, default_tab: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Help")

        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(PopdownTitle("Help for the Princeton Open Ventilator Monitor"))

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

        drilldown_rotary = QtWidgets.QLabel(
            r"""
        <p> The patient box has a screen and a dial. To use the dial:
        <ul>
        <li>Press to silence the buzzer</li>
        <li>Turn to select items from the menu (item number is shown in the top left)</li>
        <li>Press and turn to set a value</li>
        <li>Reset menu item only: Press and turn to activate the reset; release while the meter is full to reset the alarm settings.</li>
        <li>Box name menu item only: Press and turn to see sub-menu items.</li>
        </ul>
        """
        )
        drilldown_rotary.setWordWrap(True)
        tabs.addTab(drilldown_rotary, "Patient box")

        version = get_version() or "<unknown>"
        layout.addWidget(QtWidgets.QLabel(f"Version: {version}"))

        self.button = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        layout.addWidget(self.button)

        self.button.accepted.connect(self.close)

        tabs.setCurrentIndex(default_tab)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    if "Fusion" in QtWidgets.QStyleFactory.keys():
        QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    else:
        print("Fusion style is not available, display may be platform dependent")

    dialog = HelpDialog()

    gis = GraphInfo()

    with open(style_path) as f:
        s = Template(f.read())
        t = s.substitute(gis.graph_pens)
        dialog.setStyleSheet(t)

    dialog.show()
    sys.exit(app.exec_())
