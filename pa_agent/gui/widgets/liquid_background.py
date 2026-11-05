"""Ambient liquid-glass canvas used behind the PA Agent workbench.

The canvas replaces the flat terminal background with a very restrained
Apple-style material: a near-black base, three low-opacity colour fields and
a soft top sheen.  Everything is painted once per resize; there is no timer,
so the effect costs nothing while the app is idle.
"""
from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QRadialGradient
from PyQt6.QtWidgets import QWidget


class LiquidBackdrop(QWidget):
    """A deep neutral canvas with subtle aurora glows behind glass panels."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workbench")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAutoFillBackground(False)

    # ── Painting ──────────────────────────────────────────────────────────
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        base = QLinearGradient(0, 0, 0, rect.height())
        base.setColorAt(0.0, QColor("#090A0E"))
        base.setColorAt(0.52, QColor("#0A0B10"))
        base.setColorAt(1.0, QColor("#07080B"))
        painter.fillRect(rect, base)

        # Three wide, low-opacity fields give the glass something to refract.
        self._glow(
            painter,
            rect,
            cx=0.10,
            cy=0.02,
            radius=0.62,
            color=QColor(10, 132, 255, 72),
        )
        self._glow(
            painter,
            rect,
            cx=0.92,
            cy=0.08,
            radius=0.54,
            color=QColor(191, 90, 242, 48),
        )
        self._glow(
            painter,
            rect,
            cx=0.58,
            cy=1.02,
            radius=0.60,
            color=QColor(48, 209, 88, 26),
        )

        # A single specular sweep along the top edge.
        sheen = QLinearGradient(0, 0, 0, max(1, int(rect.height() * 0.28)))
        sheen.setColorAt(0.0, QColor(255, 255, 255, 22))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillRect(rect, sheen)

        # Very light vignette to keep the eye on the content.
        vignette = QRadialGradient(
            QPointF(rect.width() * 0.5, rect.height() * 0.44),
            max(rect.width(), rect.height()) * 0.78,
        )
        vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
        vignette.setColorAt(0.72, QColor(0, 0, 0, 18))
        vignette.setColorAt(1.0, QColor(0, 0, 0, 58))
        painter.fillRect(rect, vignette)

    @staticmethod
    def _glow(
        painter: QPainter,
        rect,
        *,
        cx: float,
        cy: float,
        radius: float,
        color: QColor,
    ) -> None:
        gradient = QRadialGradient(
            QPointF(rect.width() * cx, rect.height() * cy),
            max(rect.width(), rect.height()) * radius,
        )
        inner = QColor(color)
        gradient.setColorAt(0.0, inner)
        mid = QColor(color)
        mid.setAlpha(max(0, color.alpha() // 3))
        gradient.setColorAt(0.55, mid)
        gradient.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
        painter.fillRect(rect, gradient)
