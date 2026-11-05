"""Five-step analysis rail rendered as a quiet Apple-style timeline."""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

_DEFAULT_NAMES = ["数据", "快照", "诊断", "决策", "追问"]
_DEFAULT_CAPTIONS = ["等待连接", "未获取", "等待阶段一", "等待阶段二", "等待完成"]

_STATUS_COLORS = {
    "idle": QColor("#3A3A3C"),
    "done": QColor("#30D158"),
    "active": QColor("#0A84FF"),
    "error": QColor("#FF453A"),
}


class FlowBar(QWidget):
    """A five-step horizontal rail with a connecting hairline.

    The public API is identical to the previous widget: ``set_step_status``,
    ``set_step_caption`` and ``reset_all``.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("flowBar")
        self.setMinimumHeight(66)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._statuses = ["idle"] * len(_DEFAULT_NAMES)
        self._captions = list(_DEFAULT_CAPTIONS)

    # ── Public API ─────────────────────────────────────────────────────────
    def set_step_status(self, index: int, status: str) -> None:
        if 0 <= index < len(self._statuses):
            self._statuses[index] = status if status in _STATUS_COLORS else "idle"
            self.update()

    def set_step_caption(self, index: int, text: str) -> None:
        if 0 <= index < len(self._captions):
            self._captions[index] = text
            self.update()

    def reset_all(self) -> None:
        self._statuses = ["idle"] * len(_DEFAULT_NAMES)
        self._captions = list(_DEFAULT_CAPTIONS)
        self.update()

    # ── Painting ───────────────────────────────────────────────────────────
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        # Liquid-glass capsule.
        painter.setPen(QPen(QColor(255, 255, 255, 24), 1))
        painter.setBrush(QColor(255, 255, 255, 11))
        painter.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 18, 18)

        count = len(_DEFAULT_NAMES)
        left = 26.0
        right = rect.width() - 26.0
        usable = max(1.0, right - left)
        step = usable / count
        rail_y = 25.0

        # Connecting hairline, split into a subtle progress track.
        painter.setPen(QPen(QColor(255, 255, 255, 24), 1.5))
        painter.drawLine(QPointF(left + step * 0.5, rail_y), QPointF(right - step * 0.5, rail_y))

        name_font = QFont(self.font())
        name_font.setPixelSize(12)
        name_font.setWeight(QFont.Weight.DemiBold)
        cap_font = QFont(self.font())
        cap_font.setPixelSize(10)

        for i, name in enumerate(_DEFAULT_NAMES):
            cx = left + step * (i + 0.5)
            status = self._statuses[i]
            color = _STATUS_COLORS[status]
            center = QPointF(cx, rail_y)

            if status == "active":
                painter.setPen(Qt.PenStyle.NoPen)
                glow = QColor(color.red(), color.green(), color.blue(), 38)
                painter.setBrush(glow)
                painter.drawEllipse(center, 11, 11)

            if status == "done":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(center, 5, 5)
                # A very small check mark signals “complete” without a badge.
                pen = QPen(QColor("#07110A"), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawLine(QPointF(cx - 2.2, rail_y), QPointF(cx - 0.4, rail_y + 1.8))
                painter.drawLine(QPointF(cx - 0.4, rail_y + 1.8), QPointF(cx + 2.4, rail_y - 1.6))
            else:
                painter.setPen(QPen(color, 1.5))
                painter.setBrush(QColor("#0B0C10") if status == "idle" else color)
                painter.drawEllipse(center, 4.5, 4.5)

            painter.setFont(name_font)
            name_color = QColor("#F5F5F7") if status in {"done", "active"} else QColor("#8E8E93")
            painter.setPen(name_color)
            name_rect = QRectF(cx - step * 0.5, 40.0, step, 16.0)
            painter.drawText(
                name_rect,
                int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                name,
            )

            painter.setFont(cap_font)
            painter.setPen(QColor("#8E8E93"))
            cap_rect = QRectF(cx - step * 0.5, 55.0, step, 14.0)
            painter.drawText(
                cap_rect,
                int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                self._captions[i],
            )
