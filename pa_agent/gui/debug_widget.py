"""DebugWidget — Tab 3 debug panel.

Displays all AI turns in the current session with full prompt/response detail,
copy buttons, JSON export, and API-key masking.

Design reference: design.md §B.11 (Tab3)
Tasks: 16.1, 16.2, 16.3, 16.4
"""
from __future__ import annotations

import json
import logging

from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt

from pa_agent.util.mask_secret import mask_secret
from pa_agent.config.paths import RECORDS_PENDING_DIR

logger = logging.getLogger(__name__)


class DebugWidget(QWidget):
    """Tab 3 debug panel.

    Left side: QListWidget listing all turns (Stage1, Stage2, Followup-N …).
    Right side: 4 read-only QTextEdit blocks:
        1. System prompt
        2. User prompt
        3. Raw response (HTTP status, headers, body, reasoning_content, content,
           usage, request_id)
        4. Validation / retry / exception classification

    Turn data model (dict):
        label           : str   — e.g. "Stage1", "Stage2", "Followup-1"
        system_prompt   : str
        user_prompt     : str
        raw_response    : dict  — AIReply.raw dict
        validation_info : str   — validation result or exception info

    Parameters
    ----------
    api_key:
        Plaintext API key to mask in all displayed text.  Defaults to "".
    parent:
        Optional parent widget.
    """

    def __init__(
        self,
        api_key: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._api_key = api_key
        self._turns: list[dict] = []
        self._setup_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 12)
        outer.setSpacing(8)

        # ── Main splitter: list (left) | detail (right) ───────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: turn list
        left_widget = QWidget()
        left_widget.setMinimumWidth(210)
        left_widget.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        turn_title = QLabel("会话轮次")
        turn_title.setObjectName("cardMeta")
        left_layout.addWidget(turn_title)
        self._list_widget = QListWidget()
        self._list_widget.currentRowChanged.connect(self._on_turn_selected)
        left_layout.addWidget(self._list_widget, stretch=1)
        splitter.addWidget(left_widget)

        # Right: 2×2 prompt fields + button row.  A 2×2 grid keeps each editor
        # readable in the 860 px sidebar instead of stacking four 50 px boxes.
        right_widget = QWidget()
        right_widget.setMinimumWidth(420)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self._system_edit = self._make_text_edit("System Prompt")
        self._user_edit = self._make_text_edit("User Prompt")
        self._response_edit = self._make_text_edit("Raw Response")
        self._validation_edit = self._make_text_edit("Validation / Exception")

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)
        fields = (
            ("System Prompt", self._system_edit),
            ("User Prompt", self._user_edit),
            ("Raw Response", self._response_edit),
            ("Validation / Exception", self._validation_edit),
        )
        for index, (label, edit) in enumerate(fields):
            row = (index // 2) * 2
            col = index % 2
            cap = QLabel(label)
            cap.setObjectName("fieldCaption")
            grid.addWidget(cap, row, col)
            edit.setMinimumHeight(92)
            grid.addWidget(edit, row + 1, col)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(3, 1)
        right_layout.addLayout(grid, stretch=1)

        # Button row
        right_layout.addLayout(self._build_button_row())

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([230, 620])

        outer.addWidget(splitter)

    def _make_text_edit(self, placeholder: str = "") -> QTextEdit:
        edit = QTextEdit()
        edit.setReadOnly(True)
        edit.setPlaceholderText(placeholder)
        return edit

    def _build_button_row(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        buttons: list[QPushButton] = []
        btn_copy_system = QPushButton("复制 system")
        btn_copy_system.clicked.connect(self._copy_system)
        buttons.append(btn_copy_system)

        btn_copy_user = QPushButton("复制 user")
        btn_copy_user.clicked.connect(self._copy_user)
        buttons.append(btn_copy_user)

        btn_copy_response = QPushButton("复制 response")
        btn_copy_response.clicked.connect(self._copy_response)
        buttons.append(btn_copy_response)

        btn_export = QPushButton("导出本轮 JSON")
        btn_export.clicked.connect(self._export_turn_json)
        buttons.append(btn_export)

        btn_copy_debug = QPushButton("复制调试信息")
        btn_copy_debug.setToolTip(
            "复制当前轮次的 Raw Response + Validation / Exception，便于粘贴给 AI 排查问题"
        )
        btn_copy_debug.clicked.connect(self._copy_debug_info)
        buttons.append(btn_copy_debug)

        # 3 + 2 layout keeps the row inside the narrow analyst card instead of
        # letting five wide buttons force the whole splitter past its edge.
        for index, button in enumerate(buttons):
            grid.addWidget(button, index // 3, index % 3)
        for col in range(3):
            grid.setColumnStretch(col, 1)
        return grid

    # ── Public API ────────────────────────────────────────────────────────────

    def add_turn(self, turn_data: dict) -> None:
        """Append a turn to the list.

        Parameters
        ----------
        turn_data:
            Dict with keys: label, system_prompt, user_prompt,
            raw_response, validation_info.
        """
        self._turns.append(turn_data)
        label = turn_data.get("label", f"Turn-{len(self._turns)}")

        # Append cache hit rate to the label if available
        raw = turn_data.get("raw_response") or {}
        usage = raw.get("usage") or {}
        hit_pct = usage.get("cache_hit_rate_pct")
        if hit_pct is not None and hit_pct > 0:
            label = f"{label}  [{hit_pct:.0f}% 缓存]"

        item = QListWidgetItem(label)
        self._list_widget.addItem(item)
        # Auto-select the newly added turn
        self._list_widget.setCurrentRow(len(self._turns) - 1)

    def clear(self) -> None:
        """Clear all turns from the widget."""
        self._turns.clear()
        self._list_widget.clear()
        self._system_edit.clear()
        self._user_edit.clear()
        self._response_edit.clear()
        self._validation_edit.clear()

    def focus_last_turn(self) -> None:
        """Select the most recent turn in the list."""
        if self._list_widget.count() > 0:
            self._list_widget.setCurrentRow(self._list_widget.count() - 1)

    def focus_exception_turn(self) -> bool:
        """Select the ⚠ 异常 turn if present, else the last turn."""
        for row in range(self._list_widget.count() - 1, -1, -1):
            item = self._list_widget.item(row)
            if item is not None and "异常" in item.text():
                self._list_widget.setCurrentRow(row)
                return True
        self.focus_last_turn()
        return False

    def build_debug_bundle(self, row: int | None = None) -> str:
        """Build text for bug reports: validation + raw response (+ optional prompts)."""
        if row is None:
            row = self._current_row()
        if row < 0 or row >= len(self._turns):
            return ""
        turn = self._turns[row]
        parts: list[str] = []
        label = turn.get("label", f"Turn-{row}")
        parts.append(f"=== {label} ===")
        validation = turn.get("validation_info", "")
        if validation:
            parts.append("\n--- Validation / Exception ---\n")
            parts.append(validation)
        raw = turn.get("raw_response", {})
        if raw:
            parts.append("\n--- Raw Response ---\n")
            parts.append(self._format_raw_response(raw))
        system = turn.get("system_prompt", "")
        user = turn.get("user_prompt", "")
        if system or user:
            parts.append("\n--- System Prompt ---\n")
            parts.append(system)
            parts.append("\n--- User Prompt ---\n")
            parts.append(user)
        return self._mask("\n".join(parts).strip())

    # ── Turn selection ────────────────────────────────────────────────────────

    def _on_turn_selected(self, row: int) -> None:
        if row < 0 or row >= len(self._turns):
            self._system_edit.clear()
            self._user_edit.clear()
            self._response_edit.clear()
            self._validation_edit.clear()
            return

        turn = self._turns[row]
        self._system_edit.setPlainText(self._mask(turn.get("system_prompt", "")))
        self._user_edit.setPlainText(self._mask(turn.get("user_prompt", "")))
        self._response_edit.setPlainText(
            self._mask(self._format_raw_response(turn.get("raw_response", {})))
        )
        self._validation_edit.setPlainText(
            self._mask(turn.get("validation_info", ""))
        )

    def _current_row(self) -> int:
        return self._list_widget.currentRow()

    # ── Masking ───────────────────────────────────────────────────────────────

    def _mask(self, text: str) -> str:
        """Replace all occurrences of the plaintext API key with its masked form."""
        if not self._api_key or not text:
            return text
        masked = mask_secret(self._api_key)
        return text.replace(self._api_key, masked)

    # ── Formatting ────────────────────────────────────────────────────────────

    @staticmethod
    def _format_raw_response(raw: dict) -> str:
        """Render the raw response dict as a human-readable string.

        Promotes KV-cache hit stats to the top of the output so they're
        immediately visible without scrolling.
        """
        if not raw:
            return ""
        try:
            usage = raw.get("usage") or {}
            prompt_tokens = usage.get("prompt_tokens", 0)
            cached_tokens = usage.get("cached_prompt_tokens", 0)
            miss_tokens = usage.get("cache_miss_tokens", prompt_tokens - cached_tokens)
            hit_pct = usage.get("cache_hit_rate_pct")
            completion_tokens = usage.get("completion_tokens", 0)

            if prompt_tokens > 0:
                if hit_pct is None:
                    hit_pct = cached_tokens / prompt_tokens * 100.0
                cache_banner = (
                    f"═══ KV Cache ═══\n"
                    f"  命中：{cached_tokens:,} tokens ({hit_pct:.1f}%)  "
                    f"未命中：{miss_tokens:,} tokens\n"
                    f"  输入合计：{prompt_tokens:,}  输出：{completion_tokens:,}\n"
                    "═══════════════\n\n"
                )
            else:
                cache_banner = ""

            body = json.dumps(raw, ensure_ascii=False, indent=2)
            return f"{cache_banner}{body}"
        except (TypeError, ValueError):
            return str(raw)

    # ── Button handlers ───────────────────────────────────────────────────────

    def _copy_system(self) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._system_edit.toPlainText())

    def _copy_user(self) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._user_edit.toPlainText())

    def _copy_response(self) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._response_edit.toPlainText())

    def _copy_debug_info(self) -> None:
        from PyQt6.QtWidgets import QApplication

        text = self.build_debug_bundle()
        if not text:
            QMessageBox.information(self, "复制调试信息", "没有可复制的调试内容，请先完成一轮分析。")
            return
        QApplication.clipboard().setText(text)
        QMessageBox.information(
            self,
            "已复制",
            "已复制当前轮次的调试信息到剪贴板，可粘贴给 AI 协助排查。",
        )

    def _export_turn_json(self) -> None:
        """Write the current turn's data to records/pending/<label>.debug-<row>.json."""
        row = self._current_row()
        if row < 0 or row >= len(self._turns):
            QMessageBox.information(self, "导出", "没有选中的轮次。")
            return

        turn = self._turns[row]
        label = turn.get("label", f"turn-{row}")
        # Sanitise label for use in filename
        safe_label = label.replace(" ", "_").replace("/", "-")
        filename = f"{safe_label}.debug-{row}.json"

        try:
            RECORDS_PENDING_DIR.mkdir(parents=True, exist_ok=True)
            out_path = RECORDS_PENDING_DIR / filename
            out_path.write_text(
                json.dumps(turn, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("Debug turn exported to %s", out_path)
            QMessageBox.information(self, "导出成功", f"已写入：\n{out_path}")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to export debug turn: %s", exc)
            QMessageBox.critical(self, "导出失败", str(exc))

