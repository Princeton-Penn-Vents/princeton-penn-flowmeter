from typing import List

class SpiDev:
    max_speed_hz: int
    def open(self, bus: int, device: int):
        pass
    def xfer2(self, data: List[int]) -> List[int]:
        pass
    def __enter__(self) -> SpiDev: ...
    def __exit__(self, *exc) -> None: ...
