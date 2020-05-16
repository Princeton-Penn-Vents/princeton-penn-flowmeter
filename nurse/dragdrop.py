from __future__ import annotations

from nurse.qt import (
    QtWidgets,
    QtGui,
    QtCore,
    Qt,
    swap_grid,
)

from nurse.gen_record_gui import GenRecordGUI

from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Protocol

    class DragGridProtocol(Protocol, QtWidgets.QWidget):
        @property
        def MIME_NAME(self) -> str:
            ...

        @property
        def _start_pos(self) -> Optional[QtGui.QMouseEvent]:
            ...

        @_start_pos.setter
        def _start_pos(self, value: Optional[QtGui.QMouseEvent]) -> None:
            ...


class DragDropGridMixin:
    # Requirements:
    # self.parent().grid_layout (not checked by mypy)
    # And now drop_final_row_or_column_if_needed is required too (so now it's pretty
    # specialized. Oh, well.)

    def mime_type(self: DragGridProtocol) -> str:
        return f"application/{self.MIME_NAME}"

    def __init__(self: DragGridProtocol, *args, **kwargs):
        self.setAcceptDrops(True)
        self._start_pos: Optional[QtGui.QMouseEvent] = None

    def mousePressEvent(self: DragGridProtocol, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._start_pos = event.pos()

    def mouseMoveEvent(self: DragGridProtocol, evt: QtGui.QMouseEvent) -> None:
        if self._start_pos is None or not (evt.buttons() & Qt.LeftButton):
            return
        if (
            evt.pos() - self._start_pos
        ).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            return

        hot_spot = evt.pos()

        mime_data = QtCore.QMimeData()
        mime_data.setData(
            self.mime_type(),
            QtCore.QByteArray.number(hot_spot.x())
            + b" "
            + QtCore.QByteArray.number(hot_spot.y()),
        )

        dpr = QtWidgets.QApplication.instance().devicePixelRatio()
        pixmap = QtGui.QPixmap(self.size() * dpr)
        pixmap.setDevicePixelRatio(dpr)
        self.render(pixmap)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        drag.setHotSpot(hot_spot)

        self.setVisible(False)
        drag.exec()

        if drag.target() and drag.source() != drag.target():
            parent = self.parent()
            swap_grid(parent.grid_layout, drag.source(), drag.target())
            for item in (drag.source(), drag.target()):
                if hasattr(item, "gen"):
                    record: GenRecordGUI = item.gen.record
                    ind = parent.grid_layout.indexOf(item)
                    x, y, _width, _height = parent.grid_layout.getItemPosition(ind)
                    record.position = (x, y)
            parent.drop_final_row_or_column_if_needed()

        self.setVisible(True)

    def dragEnterEvent(self: DragGridProtocol, evt: QtGui.QDragEnterEvent) -> None:
        if evt.mimeData().hasFormat(self.mime_type()):
            evt.accept()
            eff = QtWidgets.QGraphicsOpacityEffect(self)
            eff.setOpacity(0.5)
            self.setGraphicsEffect(eff)
        else:
            evt.ignore()

    def dragLeaveEvent(self: DragGridProtocol, evt: QtGui.QDragEnterEvent) -> None:
        self.setGraphicsEffect(None)

    def dropEvent(self: DragGridProtocol, evt):
        if evt.mimeData().hasFormat(self.mime_type()):
            evt.accept()
            self.setGraphicsEffect(None)
        else:
            evt.ignore()
