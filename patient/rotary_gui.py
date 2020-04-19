from processor.rotary import LocalRotary
from processor.setting import Setting, SelectionSetting, IncrSetting
from processor.generator import Generator
from typing import Dict

from nurse.qt import QtCore, QtWidgets, QtGui, Slot, Qt, update_textbox


class SelectionSettingGUI(QtWidgets.QComboBox):
    def __init__(self, setting: SelectionSetting):
        super().__init__()
        self.setting = setting

        for choice in setting._listing:
            self.addItem(f"{choice:g}{setting.unit if setting.unit else ''}")
        self.setCurrentIndex(setting._value)
        self.setEditable(False)
        self.currentIndexChanged.connect(self.change_rotary)

    @Slot(int)
    def change_rotary(self, index: int):
        self.setting._value = index
        print(self.setting)


class IncrSettingGUI(QtWidgets.QDoubleSpinBox):
    def __init__(self, setting: IncrSetting):
        super().__init__()
        self.setting = setting

        self.setRange(setting._min, setting._max)
        self.setSingleStep(setting._incr)
        self.setValue(setting._value)
        if setting.unit is not None:
            self.setSuffix(" " + setting.unit)

        self.valueChanged.connect(self.change_rotary)

    @Slot(float)
    def change_rotary(self, value: float):
        self.setting._value = value
        print(self.setting)


class DisplaySettingGUI(QtWidgets.QWidget):
    def __init__(self, setting: Setting):
        super().__init__(f"{setting.value:g}")


class UpdatingDisplay(QtWidgets.QTextEdit):
    def __init__(self, gen: Generator):
        super().__init__()

        self.gen = gen
        self.setEditable = False
        self.setMinimumWidth(100)

        self.qTimer = QtCore.QTimer()
        self.qTimer.setInterval(1000)  # 1 second
        self.qTimer.timeout.connect(self.update)
        self.qTimer.start(1000)


class AlarmWidget(UpdatingDisplay):
    @Slot()
    def update(self):
        cumulative = "\n".join(f"{k}: {v:g}" for k, v in self.gen.cumulative.items())
        update_textbox(self, cumulative)


class CumulativeWidget(UpdatingDisplay):
    @Slot()
    def update(self):
        expand = lambda s: "".join(f"\n  {k}: {v:g}" for k, v in s.items())
        active_alarms = "\n".join(
            f"{k}: {expand(v)}" for k, v in self.gen.alarms.items()
        )
        update_textbox(self, active_alarms)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, rotary: LocalRotary, gen: Generator):
        super().__init__()

        main = QtWidgets.QWidget()
        self.setCentralWidget(main)
        layout = QtWidgets.QHBoxLayout()
        main.setLayout(layout)

        form_layout = QtWidgets.QFormLayout()
        layout.addLayout(form_layout)

        for setting in rotary.values():
            if isinstance(setting, IncrSetting):
                widget = IncrSettingGUI(setting)
            elif isinstance(setting, SelectionSetting):
                widget = SelectionSettingGUI(setting)
            else:
                widget = DisplaySettingGUI(setting)

            form_layout.addRow(setting.name, widget)

        alarms_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(alarms_layout)

        alarms_layout.addWidget(CumulativeWidget(gen), 1)
        alarms_layout.addWidget(AlarmWidget(gen), 1)
