"""5-metric summary card strip for the AI panel header."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

_DEFAULT_METRICS = [
    ("当前趋势", "—"),
    ("当前市场周期", "—"),
    ("下一个市场周期", "—"),
    ("支撑区", "—"),
    ("阻力区", "—"),
]


class _MetricCard(QFrame):
    """Single metric card with a label and a value."""

    def __init__(
        self,
        title: str,
        value: str = "—",
        *,
        primary: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setMinimumWidth(0)
        self.setMinimumHeight(76)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setObjectName("metricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(7)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._title = QLabel(title)
        self._title.setObjectName("metricTitle")
        self._title.setWordWrap(False)
        layout.addWidget(self._title)

        self._value = QLabel(value)
        self._value.setWordWrap(True)
        self._value.setMinimumWidth(0)
        self._value.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
        self._value.setObjectName(
            "metricValuePrimary" if primary else "metricValue"
        )
        layout.addWidget(self._value)

    def set_value(self, text: str) -> None:
        """Update the displayed value."""
        self._value.setText(text)


class SummaryStrip(QWidget):
    """Responsive strip of five metric cards.

    Parameters
    ----------
    parent:
        Optional parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("summaryStrip")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setHorizontalSpacing(10)
        self._layout.setVerticalSpacing(8)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._cards: list[_MetricCard] = []
        for idx, (title, value) in enumerate(_DEFAULT_METRICS):
            card = _MetricCard(title, value, primary=(idx == 0))
            self._cards.append(card)
        self._columns = 0
        self._relayout()

    def set_metrics(self, metrics: dict[str, str]) -> None:
        """Update card values from a mapping.

        Parameters
        ----------
        metrics:
            Dict of ``{title: value}``. Only keys that match a card title are
            applied.
        """
        for card in self._cards:
            title = card._title.text()
            if title in metrics:
                card.set_value(metrics[title])

    def reset(self) -> None:
        """Reset every card value to the default em-dash."""
        for card in self._cards:
            card.set_value("—")

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._relayout()

    def _target_columns(self) -> int:
        return 5

    def _relayout(self) -> None:
        columns = self._target_columns()
        if columns == self._columns and self._layout.count() == len(self._cards):
            return
        self._columns = columns
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget() is not None:
                item.widget().setParent(None)
        for idx, card in enumerate(self._cards):
            row = idx // columns
            col = idx % columns
            self._layout.addWidget(card, row, col)
        for col in range(5):
            self._layout.setColumnStretch(col, 1 if col < columns else 0)
