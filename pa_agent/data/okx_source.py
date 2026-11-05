"""OKX spot K-line data source (public REST API, no API key required)."""
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

_BASE_URL = "https://www.okx.com"

#: Our lowercase timeframe id → OKX bar id (1h = 1H).
_TF_MAP: dict[str, str] = {
    "1h": "1H",
}


class OkxSource(DataSource):
    """Public OKX spot candles (``BTC-USDT`` instruments)."""

    def __init__(self) -> None:
        self._symbol: str = ""
        self._inst_id: str = ""
        self._timeframe: str = ""
        self._connected: bool = False
        self._client = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        import httpx

        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(15.0, connect=8.0),
                headers={"User-Agent": "PA-Agent/0.1 (+okx-public-data)"},
                follow_redirects=True,
            )
        self._connected = True
        logger.info("OkxSource connected (public REST)")

    def disconnect(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception as exc:  # noqa: BLE001
                logger.debug("OKX client close failed: %s", exc)
            self._client = None
        self._connected = False
        logger.info("OkxSource disconnected")

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
        self._inst_id = f"{base}-{quote}"
        self._timeframe = timeframe
        logger.info("OkxSource subscribed: %s %s", self._inst_id, timeframe)

    def unsubscribe(self) -> None:
        self._symbol = ""
        self._inst_id = ""
        self._timeframe = ""
        logger.info("OkxSource unsubscribed")

    # ── Data fetch ────────────────────────────────────────────────────────────

    def latest_snapshot(self, n: int) -> list[KlineBar]:
        """Return up to *n* bars newest-first (index 0 may be the forming bar)."""
        if not self._connected:
            raise DataSourceTransientError("OKX 数据源未连接")
        if not self._inst_id or not self._timeframe:
            raise DataSourceTransientError("OKX 数据源未订阅交易对/周期")

        rows = self._fetch_candles(max(int(n), 1))
        if not rows:
            raise DataSourceTransientError(
                f"OKX 返回空数据：{self._inst_id} {self._timeframe}"
            )

        now_ms = int(time.time() * 1000)
        bars: list[KlineBar] = []
        for i, row in enumerate(rows[:n]):
            try:
                ts_open = int(row[0])
                confirm = str(row[8]) if len(row) > 8 else ""
                bar = KlineBar(
                    seq=i + 1,
                    ts_open=ts_open,
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                    amount=float(row[7]) if len(row) > 7 and row[7] else 0.0,
                    # confirm == "1" → candle closed; "0" → still forming.
                    closed=(confirm == "1") if confirm else ts_open < now_ms,
                )
            except (TypeError, ValueError, IndexError) as exc:
                raise DataSourceTransientError(
                    f"OKX K 线数据格式异常：{exc}"
                ) from exc
            bars.append(normalize_kline_bar(bar))
        return bars

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _fetch_candles(self, n: int) -> list[list]:
        """Fetch the newest *n* candles, paging older history as needed."""
        need = max(n, 1)
        first_limit = min(300, need)
        rows = self._request(
            "/api/v5/market/candles",
            {
                "instId": self._inst_id,
                "bar": _TF_MAP[self._timeframe],
                "limit": first_limit,
            },
        )
        if not isinstance(rows, list):
            return []

        # Candles endpoint caps at 300 rows; history endpoint adds 100 at a time.
        for _ in range(50):
            if len(rows) >= need or not rows:
                break
            oldest_ts = str(rows[-1][0])
            older = self._request(
                "/api/v5/market/history-candles",
                {
                    "instId": self._inst_id,
                    "bar": _TF_MAP[self._timeframe],
                    "after": oldest_ts,
                    "limit": min(100, need - len(rows)),
                },
            )
            if not isinstance(older, list) or not older:
                break
            known = {str(r[0]) for r in rows}
            fresh = [r for r in older if str(r[0]) not in known]
            if not fresh:
                break
            rows.extend(fresh)

        return rows[:need]

    def _request(self, path: str, params: dict) -> list:
        if self._client is None:
            raise DataSourceTransientError("OKX HTTP 客户端未初始化")

        try:
            resp = self._client.get(f"{_BASE_URL}{path}", params=params)
        except Exception as exc:  # noqa: BLE001 — network/timeout
            raise DataSourceTransientError(
                f"OKX 连接失败：{type(exc).__name__}。若在国内网络，请开启代理后重启程序。"
            ) from exc

        if resp.status_code != 200:
            body = resp.text[:200].replace("\n", " ")
            if resp.status_code in (403, 451):
                raise DataSourceTransientError(
                    f"OKX 接口在当前网络被限制（HTTP {resp.status_code}）。请开启代理后重启程序再试。"
                )
            raise DataSourceTransientError(
                f"OKX 接口 HTTP {resp.status_code}：{body}"
            )

        try:
            payload = resp.json()
        except ValueError as exc:
            raise DataSourceTransientError("OKX 返回了非 JSON 响应") from exc

        if not isinstance(payload, dict) or str(payload.get("code")) != "0":
            msg = ""
            data = payload.get("data") if isinstance(payload, dict) else None
            if isinstance(data, list) and data and isinstance(data[0], dict):
                msg = str(data[0].get("sMsg") or "")
            if not msg and isinstance(payload, dict):
                msg = str(payload.get("msg") or "")
            raise DataSourceTransientError(f"OKX 接口错误：{msg or payload}")

        data = payload.get("data")
        return data if isinstance(data, list) else []
