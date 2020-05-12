from __future__ import annotations

from dataclasses import dataclass, field

from processor.gen_record import GenRecord
from nurse.qt import Signal, QtCore


class RecordSignals(QtCore.QObject):
    title_changed = Signal()


@dataclass
class GenRecordGUI(GenRecord):
    master_signal: RecordSignals = field(default_factory=RecordSignals)

    def title_changed(self) -> None:
        self.master_signal.title_changed.emit()
