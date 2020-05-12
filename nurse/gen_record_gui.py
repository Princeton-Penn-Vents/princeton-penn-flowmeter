from __future__ import annotations

from dataclasses import dataclass, field

from processor.gen_record import GenRecord
from nurse.qt import Signal, QtCore


class RecordSignals(QtCore.QObject):
    title_changed = Signal()
    mac_changed = Signal()
    sid_changed = Signal()


@dataclass
class GenRecordGUI(GenRecord):
    master_signal: RecordSignals = field(default_factory=RecordSignals)

    def title_changed(self) -> None:
        self.master_signal.title_changed.emit()

    def mac_changed(self) -> None:
        self.master_signal.mac_changed.emit()

    def sid_changed(self) -> None:
        self.master_signal.sid_changed.emit()
