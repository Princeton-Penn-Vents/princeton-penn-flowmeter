from processor.setting import DisplaySetting, SelectionSetting
from pathlib import Path
from typing import Optional, List


DIR = Path(__file__).parent.resolve()
(DIR.parent / "device_log").mkdir(exist_ok=True)


class FilenameSetting(DisplaySetting):
    def __init__(self, name):
        super().__init__("", name=name)

    @property
    def value(self) -> str:
        files = sorted(Path(DIR.parent / "device_log").glob("*"))
        string = str(files[-1].name) if files else "No file"
        return string

    # Currently does not work remotely
    @value.setter
    def value(self, value: str):
        self._value = value


class CurrentSetting(SelectionSetting):
    def __init__(self, name):
        listing = ["1s", "3s", "5s", "10s", "20s", "30s", "60s"]

        self._F: Optional[List[float]] = None
        self._P: Optional[List[float]] = None
        self._RR: Optional[List[float]] = None

        super().__init__(3, listing, name=name)

    def from_processor(self, F: List[float], P: List[float], RR: List[float]):
        self._F = F
        self._P = P
        self._RR = RR

    @property
    def lcd_name(self):
        if self._F is None or self._P is None:
            return self._name

        F = self._F[self._value]
        P = self._P[self._value]
        RR = self._RR[self._value]

        return f"F:{F:<6.1f} P:{P:.2f}"

    # For the GUI
    def print_setting(self, value: int):
        ave_t = self._listing[value]
        if self._F is None or self._P is None or self._RR is None:
            return f"{ave_t} -> No average yet"
        F = self._F[value]
        P = self._P[value]
        RR = self._RR[value]

        return f"{ave_t} -> F:{F:.5g} P:{P:5.5g} RR:{RR:<5.0f}"

    def __str__(self):
        ave_t = self._listing[self._value]
        if self._F is None or self._P is None:
            return f"         {ave_t:>3}"

        RR = self._RR[self._value]
        return f"RR:{RR:<5.0f}{ave_t:>3}"
