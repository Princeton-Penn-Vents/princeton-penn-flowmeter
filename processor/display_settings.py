from processor.setting import DisplaySetting, SelectionSetting
from pathlib import Path
from typing import Optional, List, Sequence


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

    @property
    def default(self) -> float:
        return 0.0

    @default.setter
    def default(self, val: float):
        pass


class CurrentSetting(SelectionSetting):
    def __init__(self, name, *, listing: Sequence[int], default: int):
        string_listing = [f"{s}s" for s in listing]

        self._F: Optional[List[float]] = None
        self._P: Optional[List[float]] = None

        super().__init__(default, string_listing, name=name)

    def from_processor(self, F: List[float], P: List[float]):
        self._F = F
        self._P = P

    @property
    def lcd_name(self):
        if self._F is None or self._P is None:
            return self._name

        F = self._F[self._value]
        P = self._P[self._value]

        return f"F:{F:<6.1f} P:{P:.2f}"

    # For the GUI
    def print_setting(self, value: int):
        ave_t = self._listing[value]
        if self._F is None or self._P is None:
            return f"{ave_t} -> No average yet"
        F = self._F[value]
        P = self._P[value]

        return f"{ave_t} -> F:{F:.5g} P:{P:5.5g}"

    def __str__(self):
        ave_t = self._listing[self._value]
        return f"Current: {ave_t:>3}"
