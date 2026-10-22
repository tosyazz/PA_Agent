"""「控制台」标签页：把 stdout / stderr 显示在主界面里。"""
from __future__ import annotations

import html

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pa_agent.gui.console_stream import CONSOLE_BUFFER

_LEVEL_COLORS = {
    "ERROR": "#f87171",
    "CRITICAL": "#f87171",
    "WARNING": "#fbbf24",
    "DEBUG": "#64748b",
}


class ConsolePanel(QWidget):
    """只读控制台：轮询 ConsoleBuffer 并渲染。"""

    _POLL_MS = 250

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._edit = QPlainTextEdit(self)
        self._edit.setReadOnly(True)
        self._edit.setObjectName("consolePane")
        self._edit.setMaximumBlockCount(5000)
        self._edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        font = QFont("Cascadia Mono", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._edit.setFont(font)
        self._edit.setStyleSheet(
            "QPlainTextEdit#consolePane {"
            "  background-color: #0b0f14;"
            "  color: #cbd5e1;"
            "  border: 1px solid #1b2430;"
            "  border-radius: 10px;"
            "  padding: 8px 10px;"
            "  selection-background-color: rgba(45,212,191,0.30);"
            "}"
        )
        self._edit.setPlaceholderText("程序运行日志会显示在这里（等同原来的控制台窗口）")

        self._autoscroll = QCheckBox("自动滚动")
        self._autoscroll.setChecked(True)

        self._status = QLabel("")
        self._status.setObjectName("mutedLabel")

        clear_btn = QPushButton("清空")
        clear_btn.setToolTip("清空当前显示（不影响日志文件）")
        clear_btn.clicked.connect(self._edit.clear)

        copy_btn = QPushButton("复制全部")
        copy_btn.setToolTip("把当前控制台内容复制到剪贴板")
        copy_btn.clicked.connect(self._copy_all)

        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(8)
        bar.addWidget(QLabel("控制台"))
        bar.addWidget(self._status, 1)
        bar.addWidget(self._autoscroll)
        bar.addWidget(copy_btn)
        bar.addWidget(clear_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addLayout(bar)
        layout.addWidget(self._edit, 1)

        self._timer = QTimer(self)
        self._timer.setInterval(self._POLL_MS)
        self._timer.timeout.connect(self._drain)
        self._timer.start()

        self._pending_lines = 0

    # ── internals ────────────────────────────────────────────────────────────

    def _drain(self) -> None:
        chunk = CONSOLE_BUFFER.drain()
        if not chunk:
            return
        self._pending_lines = chunk.count("\n")
        self._append(chunk)

    def _append(self, text: str) -> None:
        scrollbar = self._edit.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 4
        cursor = self._edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._edit.setTextCursor(cursor)
        self._edit.insertPlainText(text)
        if self._autoscroll.isChecked() and at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        self._status.setText(f"共 {self._edit.blockCount()} 行")

    def _copy_all(self) -> None:
        from PyQt6.QtWidgets import QApplication

        QApplication.clipboard().setText(self._edit.toPlainText())

    def append_line(self, text: str) -> None:
        """Public hook so other code can push a line directly."""
        self._append(text if text.endswith("\n") else text + "\n")
