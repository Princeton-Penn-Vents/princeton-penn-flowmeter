from processor.rotary import LocalRotary
from processor.setting import Setting, SelectionSetting, IncrSetting
from processor.display_settings import CurrentSetting
from processor.generator import Generator

from nurse.qt import QtCore, QtWidgets, Slot, Signal, update_textbox

from typing import Optional, Callable


class RedrawSettings(QtCore.QObject):
    changed = Signal()


class RotaryGUI(LocalRotary):
    signal: RedrawSettings

    def external_update(self) -> None:
        self.signal.changed.emit()


class SelectionSettingGUI(QtWidgets.QComboBox):
    def __init__(self, setting: SelectionSetting):
        super().__init__()
        self.setting = setting

        for choice in setting._listing:
            self.addItem(f"{choice}{setting.unit if setting.unit else ''}")
        self.setCurrentIndex(setting._value)
        self.setEditable(False)
        self.currentIndexChanged.connect(self.change_rotary)

    @Slot(int)
    def change_rotary(self, index: int):
        self.setting._value = index
        print(self.setting)


class CurrentSettingGUI(QtWidgets.QComboBox):
    def __init__(self, setting: CurrentSetting, signal: RedrawSettings):
        super().__init__()
        self.setting = setting

        for i in range(len(setting)):
            self.addItem(f"{setting.print_setting(i)}")
        self.setCurrentIndex(setting._value)
        self.setEditable(False)

        signal.changed.connect(self.redraw)

    @Slot()
    def redraw(self):
        setting = self.setting
        for i in range(len(setting)):
            self.setItemText(i, f"{setting.print_setting(i)}")


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


class DisplaySettingGUI(QtWidgets.QLabel):
    def __init__(self, setting: Setting):
        super().__init__(f"{setting.value}")


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
        cumulative = "\n".join(f"{k}: {v}" for k, v in self.gen.cumulative.items())
        update_textbox(self, cumulative)


class CumulativeWidget(UpdatingDisplay):
    @Slot()
    def update(self):
        expand = lambda s: "".join(f"\n  {k}: {v}" for k, v in s.items())
        active_alarms = "\n".join(
            f"{k}: {expand(v)}" for k, v in self.gen.alarms.items()
        )
        update_textbox(self, active_alarms)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        rotary: RotaryGUI,
        gen: Generator,
        action: Optional[Callable[[], None]] = None,
    ):
        super().__init__()

        self.action = action
        rotary.signal = RedrawSettings()

        main = QtWidgets.QWidget()
        self.setCentralWidget(main)
        layout = QtWidgets.QHBoxLayout(main)

        form_layout = QtWidgets.QFormLayout()
        layout.addLayout(form_layout)

        for setting in rotary.values():
            if isinstance(setting, CurrentSetting):
                widget = CurrentSettingGUI(setting, rotary.signal)
            elif isinstance(setting, IncrSetting):
                widget = IncrSettingGUI(setting)
            elif isinstance(setting, SelectionSetting):
                widget = SelectionSettingGUI(setting)
            else:
                widget = DisplaySettingGUI(setting)

            widget.setMinimumWidth(250)
            form_layout.addRow(setting.name, widget)

        alarms_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(alarms_layout)

        alarms_layout.addWidget(CumulativeWidget(gen), 1)
        alarms_layout.addWidget(AlarmWidget(gen), 1)

    def closeEvent(self, evt):
        if self.action is not None:
            self.action()
        super().closeEvent(evt)
