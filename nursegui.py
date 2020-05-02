#!/usr/bin/env python3
import pyqtgraph as pg

# stdlib
import sys
import math
from string import Template
from pathlib import Path
import signal
import logging
from typing import Optional

from nurse.qt import (
    QtCore,
    QtWidgets,
    Qt,
    Slot,
    VBoxLayout,
    GridLayout,
)

from nurse.common import style_path, GraphInfo
from nurse.header import MainHeaderWidget
from nurse.grid import PatientSensor
from nurse.drilldown import DrilldownWidget

from processor.generator import Generator
from processor.local_generator import LocalGenerator
from processor.remote_generator import RemoteGenerator
from processor.config import init_logger, ArgumentParser
from processor.listener import FindBroadcasts

DIR = Path(__file__).parent.resolve()

logger = logging.getLogger("povm")


class MainStack(QtWidgets.QWidget):
    def __init__(
        self,
        *,
        listener: FindBroadcasts,
        displays: Optional[int],
        debug: bool,
        sim: bool,
    ):
        super().__init__()

        self.listener = listener

        layout = VBoxLayout(self)

        self.header = MainHeaderWidget(self)
        layout.addWidget(self.header)

        grid_layout = GridLayout()
        self.grid_layout = grid_layout
        layout.addLayout(grid_layout)

        self.graphs = []

        if displays:
            height = math.ceil(math.sqrt(displays))
            width = math.ceil(displays / height)

            # Avoid wiggles when updating
            for i in range(width):
                grid_layout.setColumnStretch(i, 3)

            for i in range(displays):
                gen: Generator

                if not sim:
                    gen = RemoteGenerator(address="tcp://127.0.0.1:8100")
                else:
                    gen = LocalGenerator()
                gen.rotary["Sensor ID"].value = i + 1

                gen.run()  # Close must be called

                graph = PatientSensor(gen=gen, i=i)
                self.graphs.append(graph)

                grid_layout.addWidget(graph, *reversed(divmod(i, height)))
                graph.set_plot()

        self.qTimer = QtCore.QTimer()
        self.qTimer.timeout.connect(self.update_plots)
        self.qTimer.setSingleShot(True)
        self.qTimer.start()

    def add_item(self, gen: Generator):
        ind = self.grid_layout.count()
        n_items = ind + 1
        height = math.ceil(math.sqrt(n_items))
        width = math.ceil(n_items / height)

        # Avoid wiggles when updating
        for i in range(width):
            self.grid_layout.setColumnStretch(i, 3)

        for i in range(height):
            for j in range(width):
                if self.grid_layout.itemAtPosition(i, j) is None:
                    break

        graph = PatientSensor(i=ind, gen=gen)
        self.graphs.append(graph)

        self.grid_layout.addWidget(graph, i, j)
        graph.set_plot()

    @Slot()
    def update_plots(self) -> None:
        if self.isVisible():
            for graph in self.graphs:
                graph.update_plot()
            self.qTimer.start(50)
        else:
            self.qTimer.start(500)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *, displays: Optional[int], listener: FindBroadcasts, **kwargs):
        super().__init__()
        self.setObjectName("MainWindow")

        # May be expensive, probably only enable if we multithread the draw
        # pg.setConfigOptions(antialias=True)
        pg.setConfigOption("background", (0, 0, 0, 0))

        gis = GraphInfo()

        with open(style_path) as f:
            s = Template(f.read())
            t = s.substitute(**gis.graph_pens)
            self.setStyleSheet(t)

        self.main_stack = MainStack(listener=listener, displays=displays, **kwargs)
        stacked_widget = QtWidgets.QStackedWidget()
        stacked_widget.addWidget(self.main_stack)

        self.drilldown = DrilldownWidget(parent=self)
        self.drilldown.return_btn.clicked.connect(self.drilldown_deactivate)
        stacked_widget.addWidget(self.drilldown)

        self.setCentralWidget(stacked_widget)

        self.main_stack.header.fs_exit.clicked.connect(self.close)

    @Slot()
    def drilldown_deactivate(self):
        self.drilldown.deactivate()
        stacked_widget = self.centralWidget()
        stacked_widget.setCurrentIndex(0)

    def drilldown_activate(self, i):
        self.drilldown.activate(i)
        stacked_widget = self.centralWidget()
        stacked_widget.setCurrentIndex(1)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            stacked_widget = self.centralWidget()
            if stacked_widget.currentIndex() != 0:
                self.drilldown_deactivate()

    def changeEvent(self, evt):
        super().changeEvent(evt)
        if evt.type() == QtCore.QEvent.WindowStateChange:
            self.main_stack.header.fs_exit.setVisible(
                self.windowState() & Qt.WindowFullScreen
            )

    def closeEvent(self, evt):
        for graph in self.main_stack.graphs:
            graph.gen.close()
        super().closeEvent(evt)


def main(argv, *, fullscreen: bool, debug: bool, **kwargs):

    if "Fusion" in QtWidgets.QStyleFactory.keys():
        QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    else:
        print("Fusion style is not available, display may be platform dependent")

    init_logger("nurse_log/nursegui.log")

    logger.info("Starting nursegui")

    app = QtWidgets.QApplication(argv)

    with FindBroadcasts() as listener:
        main = MainWindow(debug=debug, listener=listener, **kwargs)
        if fullscreen:
            main.showFullScreen()
        else:
            size = app.screens()[0].availableSize()
            if size.width() < 2000 or size.height() < 1200:
                main.resize(int(size.width() * 0.95), int(size.height() * 0.85))
                main.showMaximized()
            else:
                main.resize(1920, 1080)
                main.showNormal()

        def ctrl_c(_sig_num, _stack_frame):
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            main.close()

        signal.signal(signal.SIGINT, ctrl_c)
        sys.exit(app.exec_())


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument(
        "--displays", "-n", type=int, help="# of displays (Dynamic if not given)",
    )
    parser.add_argument(
        "--sim",
        action="store_true",
        help="Read from fake sim instead of remote generators",
    )

    args, unparsed_args = parser.parse_known_args()

    d = args.__dict__
    del d["config"]

    main(argv=sys.argv[:1] + unparsed_args, **d)
