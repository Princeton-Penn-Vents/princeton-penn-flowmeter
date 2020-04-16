from pathlib import Path

from nurse.qt import QtGui

# Replace with proper importlib.resources if made a package
DIR = Path(__file__).parent.absolute()
style_path = DIR / "style.css"

guicolors = {
    "ALERT": QtGui.QColor(0, 0, 100),
    "DISCON": QtGui.QColor(0, 0, 200),
}

prefill = [
    "Room 342, Joe Black, AGE 23",
    "Room 123, Jane Green, AGE 67",
    "Room 324, Jerry Mouse, AGE 82",
    "Room 243, Tom Cat, AGE 79",
    "Room 432, Mary Jones, AGE 18",
    "Room 654, June Adam, AGE 56",
    "Room 102, A. Smith, AGE 94",
    "Room 124, UNKNOWN, AGE 60",
    "Room 125, Gandalf the Grey, AGE 65",
    "Room 164, Luke Skywalker, AGE 43",
    "Room 167, Indiana Jones, AGE 82",
    "Room 169, Wonder Woman, AGE 34",
    "Room 180, Rose Flower, AGE 39",
    "Room 181, Thor, AGE 700",
    "Room 182, Beaver Cleaver, AGE 62",
    "Room 183, Ebeneezer Scrooge, AGE 99",
    "Room 184, Ru N. Ning, AGE 43",
    "Room 185, O. U. Tof, AGE 50",
    "Room 186, Good Names, AGE 77",
    "Room 187, Good Bye, AGE 59",
]


class GraphInfo:
    def __init__(self):
        # the y limits ought to be configurable.
        self.graph_labels = ["flow", "pressure", "volume"]

        self.graph_pens = {
            "flow": (120, 255, 50),
            "pressure": (255, 120, 50),
            "volume": (255, 128, 255),
        }

        self.graph_pen_qcol = {k: QtGui.QColor(*v) for k, v in self.graph_pens.items()}

        self.yLims = {"flow": (-40, 30), "pressure": (0, 20), "volume": (0, 800)}
        self.yTicks = {"flow": [-30, 0, 30], "pressure": [0, 15], "volume": [0, 750]}
        self.units = {"flow": "L/m", "pressure": "cm H2O", "volume": "mL"}
