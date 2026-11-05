"""Binance spot K-line data source (public REST API, no API key required).

Endpoint order matters for users in mainland China:
``data-api.binance.vision`` is Binance's public market-data mirror and is often
reachable when ``api.binance.com`` is blocked; we fall back to the main API.
"""
from __future__ import annotations

import logging
import time

from pa_agent.data.base import (
    DataSource,
    DataSourceTransientError,
    KlineBar,
    normalize_kline_bar,
)
from pa_agent.data.market_defaults import (
    CRYPTO_SYMBOLS,
    CRYPTO_TIMEFRAMES,
    is_valid_crypto_symbol,
    normalize_crypto_symbol,
    split_crypto_symbol,
)

logger = logging.getLogger(__name__)

_BASE_URLS: tuple[str, ...] = (
    "https://data-api.binance.vision",
    "https://api.binance.com",
)

_TF_MAP: dict[str, str] = {
    "1h": "1h",
}


class BinanceSource(DataSource):
    """Public Binance spot klines (USDT pairs by default)."""

    def __init__(self) -> None:
        self._symbol: str = ""
        self._timeframe: str = ""
        self._connected: bool = False
        self._client = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        import httpx

        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(15.0, connect=8.0),
                headers={"User-Agent": "PA-Agent/0.1 (+binance-public-data)"},
                follow_redirects=True,
            )
        self._connected = True
        logger.info("BinanceSource connected (public REST)")

    def disconnect(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Binance client close failed: %s", exc)
            self._client = None
        self._connected = False
        logger.info("BinanceSource disconnected")

    # ── Discovery ─────────────────────────────────────────────────────────────

    def list_symbols(self) -> list[str]:
        return list(CRYPTO_SYMBOLS)

    def supported_timeframes(self) -> list[str]:
        return list(CRYPTO_TIMEFRAMES)

    # ── Subscription ──────────────────────────────────────────────────────────

    def subscribe(self, symbol: str, timeframe: str) -> None:
        if timeframe not in _TF_MAP:
            raise ValueError(
                f"不支持的周期 {timeframe!r}；可选：{', '.join(_TF_MAP)}"
            )
        canonical = normalize_crypto_symbol(symbol)
        if not is_valid_crypto_symbol(canonical):
            raise ValueError(f"无效的交易对：{symbol!r}（示例：BTCUSDT）")
        base, quote = split_crypto_symbol(canonical)
        self._symbol = f"{base}{quote}"
        self._timeframe = timeframe
        logger.info("BinanceSource subscribed: %s %s", self._symbol, timeframe)

    def unsubscribe(self) -> None:
        self._symbol = ""
        self._timeframe = ""
        logger.info("BinanceSource unsubscribed")

    # ── Data fetch ────────────────────────────────────────────────────────────

    def latest_snapshot(self, n: int) -> list[KlineBar]:
        """Return up to *n* bars newest-first (index 0 may be the forming bar)."""
        if not self._connected:
            raise DataSourceTransientError("币安数据源未连接")
        if not self._symbol or not self._timeframe:
            raise DataSourceTransientError("币安数据源未订阅交易对/周期")

        need = max(int(n), 1)
        rows = self._fetch_klines(need)
        if not rows:
            raise DataSourceTransientError(
                f"币安返回空数据：{self._symbol} {self._timeframe}"
            )

        now_ms = int(time.time() * 1000)
        bars: list[KlineBar] = []
        for i, row in enumerate(reversed(rows)):
            try:
                ts_open = int(row[0])
                close_ms = int(row[6])
                bar = KlineBar(
                    seq=i + 1,
                    ts_open=ts_open,
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                    amount=float(row[7]) if len(row) > 7 else 0.0,
                    closed=close_ms < now_ms,
                )
            except (TypeError, ValueError, IndexError) as exc:
                raise DataSourceTransientError(
                    f"币安 K 线数据格式异常：{exc}"
                ) from exc
            bars.append(normalize_kline_bar(bar))
            if len(bars) >= n:
                break
        return bars

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _fetch_klines(self, n: int) -> list[list]:
        """Fetch the newest *n* klines (oldest-first), paging 1000 at a time."""
        rows: list[list] = []
        end_time: int | None = None
        for _ in range(8):
            limit = min(1000, n - len(rows))
            if limit <= 0:
                break
            params = {
                "symbol": self._symbol,
                "interval": _TF_MAP[self._timeframe],
                "limit": limit,
            }
            if end_time is not None:
                params["endTime"] = end_time
            batch = self._request("/api/v3/klines", params)
            if not isinstance(batch, list) or not batch:
                break
            rows = list(batch) + rows
            if len(rows) >= n or len(batch) < limit:
                break
            end_time = int(batch[0][0]) - 1
        return rows[-n:]

    def _request(self, path: str, params: dict):
        if self._client is None:
            raise DataSourceTransientError("币安 HTTP 客户端未初始化")

        last_error: Exception | None = None
        for base in _BASE_URLS:
            try:
                resp = self._client.get(f"{base}{path}", params=params)
            except Exception as exc:  # noqa: BLE001 — network/timeout
                last_error = DataSourceTransientError(
                    f"币安连接失败（{base}）：{type(exc).__name__}"
                )
                continue

            if resp.status_code == 200:
                try:
                    payload = resp.json()
                except ValueError:
                    last_error = DataSourceTransientError("币安返回了非 JSON 响应")
                    continue
                if isinstance(payload, dict) and payload.get("code") not in (None, 0):
                    raise DataSourceTransientError(
                        f"币安接口错误：{payload.get('msg') or payload}"
                    )
                return payload

            body = resp.text[:200].replace("\n", " ")
            if resp.status_code == 451:
                last_error = DataSourceTransientError(
                    "币安接口在当前网络被限制（HTTP 451）。请开启代理后重启程序再试。"
                )
                continue
            if resp.status_code == 400 and "-1121" in body:
                raise DataSourceTransientError(
                    f"币安没有交易对 {self._symbol}（请检查币种名称）"
                )
            last_error = DataSourceTransientError(
                f"币安接口 HTTP {resp.status_code}：{body}"
            )
            if resp.status_code in (400, 404):
                break

        if last_error is not None:
            raise last_error
        raise DataSourceTransientError("币安数据请求失败")
