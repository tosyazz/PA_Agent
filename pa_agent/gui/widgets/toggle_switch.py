"""Apple-style toggle used for the one-shot auto analysis switch."""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QRectF, QSize, Qt, QVariantAnimation
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QCheckBox, QSizePolicy, QWidget


class ToggleSwitch(QCheckBox):
    """A compact pill switch with a 160 ms eased thumb transition.

    It keeps the full :class:`QCheckBox` API (``isChecked``/``toggled``/keyboard
    handling) so existing call sites continue to work unchanged.
    """

    _TRACK_W = 42
    _TRACK_H = 24
    _THUMB = 20
    _GAP = 10

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(30)
        self._offset = 1.0 if self.isChecked() else 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim_value)
        self.toggled.connect(self._animate)

    # ── Geometry / animation ───────────────────────────────────────────────
    def sizeHint(self) -> QSize:  # noqa: N802
        fm = self.fontMetrics()
        width = self._TRACK_W + self._GAP + fm.horizontalAdvance(self.text()) + 4
        return QSize(width, 30)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return self.sizeHint()

    def _animate(self, checked: bool) -> None:
        target = 1.0 if checked else 0.0
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(target)
        self._anim.start()

    def _on_anim_value(self, value: object) -> None:
        try:
            self._offset = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return
        self.update()

    # ── Painting ───────────────────────────────────────────────────────────
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        height = self.height()
        track = QRectF(0.0, (height - self._TRACK_H) / 2.0, self._TRACK_W, self._TRACK_H)
        t = max(0.0, min(1.0, self._offset))

        off_color = QColor("#3A3A3C")
        on_color = QColor("#0A84FF")
        track_color = QColor(
            round(off_color.red() + (on_color.red() - off_color.red()) * t),
            round(off_color.green() + (on_color.green() - off_color.green()) * t),
            round(off_color.blue() + (on_color.blue() - off_color.blue()) * t),
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track, self._TRACK_H / 2.0, self._TRACK_H / 2.0)

        thumb_x = 2.0 + t * (self._TRACK_W - self._THUMB - 4.0)
        thumb = QRectF(
            thumb_x,
            (height - self._THUMB) / 2.0,
            self._THUMB,
            self._THUMB,
        )
        painter.setBrush(QColor(0, 0, 0, 45))
        painter.drawEllipse(thumb.translated(0, 1))
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(thumb)

        if self.hasFocus():
            ring = QRectF(track.adjusted(-3, -3, 3, 3))
            pen = QPen(QColor(10, 132, 255, 170), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(ring, (self._TRACK_H + 6) / 2.0, (self._TRACK_H + 6) / 2.0)

        label_x = self._TRACK_W + self._GAP
        text_rect = QRectF(label_x, 0.0, self.width() - label_x, height)
        font = QFont(self.font())
        font.setPixelSize(12)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor("#D1D1D6" if self.isEnabled() else "#6E6E73"))
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            self.text(),
        )
