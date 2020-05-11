from processor.setting import DisplaySetting, SelectionSetting
from pathlib import Path
from typing import Optional, List, Sequence
from patient.mac_address import get_mac_addr
from processor.device_names import address_to_name


DIR = Path(__file__).parent.resolve()
(DIR.parent / "device_log").mkdir(exist_ok=True)


class AdvancedSetting(SelectionSetting):
    STATIC_UPPER = False

    def __init__(self, *, rate: int = 2):

        string_listing = ["Box name", "MAC addr", "SensorID", "Log file"]

        # Sensor ID
        self.sid: int = 0

        super().__init__(0, string_listing, name="Advanced", rate=rate)

    @property
    def value(self) -> str:
        if self._value == 0:
            try:
                return address_to_name(get_mac_addr()).title()
            except ValueError:
                return "<Unknown>"
        elif self._value == 1:
            try:
                return get_mac_addr()
            except ValueError:
                return "<Unknown>"
        elif self._value == 2:
            return f"{self.sid:X}"
        elif self._value == 3:
            files = sorted(Path(DIR.parent / "device_log").glob("*"))
            string = str(files[-1].name) if files else "No file"
            return string
        else:
            raise NotImplementedError("Setting must be in range 0-3")

    @value.setter
    def value(self, value: int):
        pass

    def active(self) -> None:
        self._value = 0

    @property
    def lcd_name(self) -> str:
        return self._listing[self._value]

    # For the GUI
    def print_setting(self, value: int) -> str:
        c = self._value
        self._value = value
        res = f"{self.lcd_name}: {self.value}"
        self._value = c
        return res


class CurrentSetting(SelectionSetting):
    STATIC_UPPER = False

    def __init__(
        self, default: int, listing: Sequence[int], *, name: str, rate: int = 2
    ):
        string_listing = [f"{s}s" for s in listing]

        self._F: Optional[List[float]] = None
        self._P: Optional[List[float]] = None

        super().__init__(default, string_listing, name=name, rate=rate)

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

    def __str__(self) -> str:
        ave_t = self._listing[self._value]
        return f"Current: {ave_t:>3}"


class ResetSetting(SelectionSetting):
    def __init__(self, name: str, rate: int = 1):
        super().__init__(
            0, [f"[{x*'x':8}]" for x in range(9)] + ["RESET"], name=name, rate=rate
        )

    def active(self) -> None:
        self._value = 0

    @property
    def default(self) -> float:
        return 0.0

    @default.setter
    def default(self, val: float):
        pass

    def at_maximum(self):
        return self._value == (len(self._listing) - 1)
