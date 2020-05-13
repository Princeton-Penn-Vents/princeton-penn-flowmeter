from pathlib import Path

from nurse.qt import QtGui

# Replace with proper importlib.resources if made a package
from processor.config import get_internal_file

style_path = get_internal_file("nurse/style.css")
dialog_style_path = get_internal_file("nurse/dialogs.css")

guicolors = {
    "ALERT": QtGui.QColor(0, 0, 100),
    "DISCON": QtGui.QColor(0, 0, 200),
}

INFO_STRINGS = {
    "Avg Flow": ".0f",
    "Avg Pressure": ".0f",
    "RR": ".0f",  # (breaths/min)
    "TVe": ".0f",  # (mL)
    "PIP": ".0f",  # (cm H2O)
    "PEEP": ".0f",  # (cm H2O)
    "I:E time ratio": ".1f",
}


class GraphInfo:
    def __init__(self):
        # the y limits ought to be configurable.
        self.graph_labels = ["flow", "pressure", "volume"]
        self.graph_names = {key: key.capitalize() for key in self.graph_labels}

        self.graph_pens = {
            "flow": (120, 255, 50),
            "pressure": (255, 120, 50),
            "volume": (255, 128, 255),
        }

        self.yMax = {"flow": 300, "pressure": 100, "volume": 5000}
        self.yMin = {"flow": -300, "pressure": -100, "volume": 0}
        self.yStep = {"flow": 10, "pressure": 2, "volume": 100}

        self.graph_pen_qcol = {k: QtGui.QColor(*v) for k, v in self.graph_pens.items()}

        self.yLims = {"flow": (-20, 140), "pressure": (-1, 20), "volume": (0, 800)}
        self.units = {"flow": "L/m", "pressure": "cm H2O", "volume": "mL"}
