from pathlib import Path

from nurse.qt import QtGui

# Replace with proper importlib.resources if made a package
DIR = Path(__file__).parent.absolute()
style_path = DIR / "style.css"
dialog_style_path = DIR / "dialogs.css"

guicolors = {
    "ALERT": QtGui.QColor(0, 0, 100),
    "DISCON": QtGui.QColor(0, 0, 200),
}

prefill = [
    "Room 342, Darth Vader, AGE 45",
    "Room 123, Frodo Baggins, AGE 50",
    "Room 243, Tom Cat, AGE 79",
    "Room 324, Jerry Mouse, AGE 82",
    "Room 432, Mary Poppins, AGE UNKOWN",
    "Room 654, Willow Ufgood, AGE 56",
    "Room 102, Hermione Granger, AGE 17",
    "Room 124, UNKNOWN, AGE 60",
    "Room 125, Gandalf the Grey, AGE 63",
    "Room 164, Luke Skywalker, AGE 43",
    "Room 167, Indiana Jones, AGE 82",
    "Room 169, Wonder Woman, AGE 34",
    "Room 180, Willy Wonka, AGE 69",
    "Room 181, Thor, AGE 700",
    "Room 182, Beaver Cleaver, AGE 62",
    "Room 183, Ebeneezer Scrooge, AGE 99",
    "Room 002, Inigo Montoya, AGE 45",
    "Room 184, Ru N. Ning, AGE 43",
    "Room 185, O. U. Tof, AGE 50",
    "Room 186, Good Names, AGE 77",
]


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
