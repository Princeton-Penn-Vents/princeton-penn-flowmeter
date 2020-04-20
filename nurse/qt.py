# Names are selected to be like PySide

import os

if "PYQTGRAPH_QT_LIB" in os.environ:
    os.environ["PYQTGRAPH_QT_LIB"] = "PyQt5"

from pyqtgraph.Qt import QtCore, QtWidgets, QtGui

Qt = QtCore.Qt

try:
    Slot = QtCore.Slot
    Signal = QtCore.Signal
except AttributeError:
    Slot = QtCore.pyqtSlot
    Signal = QtCore.pyqtSignal

# Layout factory functions
def HBoxLayout(*args, **kwargs):
    layout = QtWidgets.QHBoxLayout(*args, **kwargs)
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    return layout


def VBoxLayout(*args, **kwargs):
    layout = QtWidgets.QVBoxLayout(*args, **kwargs)
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    return layout


def FormLayout(*args, **kwargs):
    layout = QtWidgets.QFormLayout(*args, **kwargs)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout


def GridLayout(*args, **kwargs):
    layout = QtWidgets.QGridLayout(*args, **kwargs)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout


def update_textbox(textbox, text):
    if textbox.toPlainText() != text:
        val = textbox.verticalScrollBar().value()
        textbox.setText(text)
        textbox.verticalScrollBar().setValue(val)
