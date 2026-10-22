"""「整点提交」开关：控制定时脚本是否在每小时执行取数 + 提交分析。

开关状态保存在 ``config/hourly_submit.json``，由桌面程序写入、由
``tools/auto_fetch_analyze.ps1`` 读取，两边解耦，不依赖注册表或计划任务状态。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from pa_agent.config.paths import CONFIG_DIR

logger = logging.getLogger(__name__)

HOURLY_SWITCH_PATH: Path = CONFIG_DIR / "hourly_submit.json"


def is_hourly_enabled(path: Path | None = None) -> bool:
    """Return whether the hourly job is enabled (defaults to True)."""
    target = path or HOURLY_SWITCH_PATH
    try:
        doc = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return True
    except Exception:  # noqa: BLE001 - a broken file must not block the UI
        return True
    return bool(doc.get("enabled", True))


def set_hourly_enabled(enabled: bool, path: Path | None = None) -> None:
    """Persist the switch state for the scheduled script to read."""
    target = path or HOURLY_SWITCH_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({"enabled": bool(enabled)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
