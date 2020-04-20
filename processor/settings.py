from processor.setting import IncrSetting, SelectionSetting
from processor.display_settings import FilenameSetting, CurrentSetting

REQUIRED = {
    "AvgWindow": SelectionSetting(2, [10, 15, 30, 60], unit="sec", name="AvgWindow"),
    "Stale Data Timeout": IncrSetting(
        8,
        min=1,
        max=20,
        incr=1,
        unit="sec",
        name="Stale Data Timeout",
        lcd_name="StaleDataTimeout",
    ),
}

LIVE_REQUIRED = {
    "Current Setting": CurrentSetting("FlowMeter... "),
    "Log Filename": FilenameSetting("Log filename"),
    "Sensor ID": IncrSetting(1, min=1, max=20, incr=1, name="Sensor ID"),  # REQUIRED
}

# This could be from YAML laster
OPTIONAL = {
    "RR Max": IncrSetting(
        30, min=10, max=90, incr=5, unit="1/min", name="RespRate Max"
    ),
    "PIP Max": IncrSetting(30, min=0, max=40, incr=1, unit="cm-H2O", name="PIP Max"),
    "PIP Min": IncrSetting(5, min=0, max=20, incr=1, unit="cm-H2O", name="PIP Min"),
    "PEEP Max": IncrSetting(8, min=0, max=15, incr=1, unit="cm-H2O", name="PEEP Max"),
    "PEEP Min": IncrSetting(0, min=0, max=15, incr=1, unit="cm-H2O", name="PEEP Min"),
    "TVe Max": IncrSetting(700, min=100, max=1000, incr=50, unit="ml", name="TVe Max"),
    "TVe Min": IncrSetting(300, min=100, max=1000, incr=50, unit="ml", name="TVe Min"),
    "TVi Max": IncrSetting(700, min=100, max=1000, incr=50, unit="ml", name="TVi Max"),
    "TVi Min": IncrSetting(300, min=100, max=1000, incr=50, unit="ml", name="TVi Min"),
}

LIVE_DICT = {**LIVE_REQUIRED, **REQUIRED, **OPTIONAL}
NURSE_DICT = {**REQUIRED, **OPTIONAL}
