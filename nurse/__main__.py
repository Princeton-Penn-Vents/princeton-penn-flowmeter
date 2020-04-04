#!/usr/bin/env python3

from PyQt5 import QtWidgets, uic, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import numpy as np
import sys
import os

class PatientSensor(QtWidgets.QWidget):
    def __init__(self, i):
        super().__init__()

        outer_layout = QtWidgets.QVBoxLayout()
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(0,0,0,0)
        self.setLayout(outer_layout)

        upper = QtWidgets.QWidget()
        outer_layout.addWidget(upper)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        upper.setLayout(layout)

        self.graph = pg.PlotWidget()
        self.graph.setLabel('left', 'Flow', units='L/m')
        self.graph.setLabel('bottom', 'Time', units='timestamps')
        layout.addWidget(self.graph)

        column = QtWidgets.QWidget()
        layout.addWidget(column)

        column_layout = QtWidgets.QVBoxLayout()
        column.setLayout(column_layout)

        name = QtWidgets.QLabel(str(i))
        name.setStyleSheet("font-size: 30px;");
        name.setAlignment(QtCore.Qt.AlignCenter)
        column_layout.addWidget(name)

        self.alert = QtWidgets.QLabel("OK")
        self.alert.setAlignment(QtCore.Qt.AlignCenter)
        column_layout.addWidget(self.alert)

        reset = QtWidgets.QPushButton("Reset")
        reset.setStyleSheet("color:black; background-color:white;");
        column_layout.addWidget(reset)

        lower = QtWidgets.QWidget()
        outer_layout.addWidget(lower)
        lower_layout = QtWidgets.QGridLayout()
        lower.setLayout(lower_layout)
        lower_layout.addWidget(QtWidgets.QLabel("MinFlow: 12.2 L/m"), 0, 0)
        lower_layout.addWidget(QtWidgets.QLabel("MaxFlow: 12.2 L/m"), 0, 1)
        lower_layout.addWidget(QtWidgets.QLabel("AveMinFlow: 12.2 L/m"), 1, 0)
        lower_layout.addWidget(QtWidgets.QLabel("TimeWindow: 20 s"), 1, 1)
        
    def set_plot(self, time, values, ok=True):
        pen = pg.mkPen(color=(0, 0, 255) if ok else (255, 0, 0), width=5)
        self.graph.plot(time, values, pen=pen)
        if ok:
            self.alert.setText("OK")
            self.alert.setStyleSheet("color:blue; border: 1px solid white;");
        else:
            self.alert.setText("ALERT")
            self.alert.setStyleSheet("color:red; border: 1px solid white;");


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setObjectName("MainWindow")

        # self.graphs = QtWidgets.QVBoxLayout()
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setObjectName("maingrid")
        self.setStyleSheet("""
            QWidget {
              background-color:black;
            }

            QLabel {
              color: white;
            }
        """);
        self.setCentralWidget(self.centralwidget)

        self.centralwidget.setLayout(layout)

        self.graphs = [PatientSensor(i) for i in range(20)]
        for i, graph in enumerate(self.graphs):
            layout.addWidget(self.graphs[i], *reversed(divmod(i, 5)))
        
        time = np.arange(1000)

        for i, graph in enumerate(self.graphs):
            flow = (np.mod(time + i*13, 100) / 10 - 2) * np.random.uniform(.9,1.1, len(time))
            self.graphs[i].set_plot(time, flow, i%7 != 1)

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
