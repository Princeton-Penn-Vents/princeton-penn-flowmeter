# Names are selected to be like PySide

import os

if "PYQTGRAPH_QT_LIB" in os.environ:
    os.environ["PYQTGRAPH_QT_LIB"] = "PyQt5"

from pyqtgraph.Qt import QtCore, QtWidgets, QtGui

Qt = QtCore.Qt

try:
    Slot = QtCore.Slot
except AttributeError:
    Slot = QtCore.pyqtSlot

# Layout factory functions
def HBoxLayout():
    layout = QtWidgets.QHBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    return layout


def VBoxLayout():
    layout = QtWidgets.QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    return layout


def FormLayout():
    layout = QtWidgets.QFormLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout


def GridLayout():
    layout = QtWidgets.QGridLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout


def update_textbox(textbox, text):
    if textbox.toPlainText() != text:
        val = textbox.verticalScrollBar().value()
        textbox.setText(text)
        textbox.verticalScrollBar().setValue(val)
