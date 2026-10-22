"""自动判断本机是否需要走本地代理（Clash 等）。

背景：TradingView 在国内直连不通，需要走 `127.0.0.1:7897` 之类的本地代理；
而境外/云电脑通常可以直连。与其把代理地址写死在启动脚本里，不如启动时探测：
本地代理端口通就用，否则留空直连。

优先级：
1. 环境变量里已经显式配置了 HTTP(S)_PROXY —— 一律尊重，不做任何改动；
2. 本地 7897 / 7890 端口可连通 —— 自动设置成该代理；
3. 否则 —— 不设代理，直连。
"""
from __future__ import annotations

import logging
import os
import socket

logger = logging.getLogger(__name__)

#: 依次尝试的本地代理端口（Clash 默认 7897，老版本/其他客户端常用 7890）
CANDIDATE_PORTS: tuple[int, ...] = (7897, 7890)

_PROBE_TIMEOUT_S = 0.25


def _say(message: str) -> None:
    """Write a startup line to the in-app console (stdout tee)."""
    try:
        print(message, flush=True)
    except Exception:  # noqa: BLE001 - a missing stdout must not break startup
        pass


def _port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=_PROBE_TIMEOUT_S):
            return True
    except OSError:
        return False


def detect_local_proxy(ports: tuple[int, ...] = CANDIDATE_PORTS) -> str:
    """Return ``http://127.0.0.1:<port>`` when a local proxy is listening."""
    for port in ports:
        if _port_open(port):
            return f"http://127.0.0.1:{port}"
    return ""


def apply_proxy_env_if_needed() -> str:
    """Set ``HTTP(S)_PROXY`` when a local proxy is available; return the proxy URL.

    Returns "" when the app should connect directly (no proxy configured and no
    local proxy listening).
    """
    existing = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if existing:
        logger.info("沿用已配置的代理：%s", existing)
        _say(f"[启动] 代理：沿用环境变量 {existing}")
        return existing

    proxy = detect_local_proxy()
    if not proxy:
        logger.info("未发现本地代理，使用直连")
        _say("[启动] 代理：未发现本地代理，直连 TradingView")
        return ""

    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        os.environ.setdefault(key, proxy)
    logger.info("检测到本地代理 %s，已启用", proxy)
    _say(f"[启动] 代理：已启用本地代理 {proxy}")
    return proxy
