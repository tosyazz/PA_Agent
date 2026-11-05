"""Crypto pair defaults and symbol normalization for the exchange data sources.

The UI shows canonical Binance-style symbols (``BTCUSDT``); each exchange
adapter converts that to its own instrument id (OKX: ``BTC-USDT``).
"""
from __future__ import annotations

import re

CRYPTO_DEFAULT_SYMBOL = "BTCUSDT"
CRYPTO_DEFAULT_TIMEFRAME = "1h"

#: Only the 1-hour timeframe is exposed by this build.
CRYPTO_TIMEFRAMES: tuple[str, ...] = ("1h",)

#: Suggestions shown in the symbol combo box.
CRYPTO_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOTUSDT",
    "LTCUSDT",
    "BCHUSDT",
    "TRXUSDT",
    "SUIUSDT",
    "TONUSDT",
    "NEARUSDT",
    "APTUSDT",
    "ARBUSDT",
    "OPUSDT",
    "PEPEUSDT",
)

# Longest first so ``FDUSD`` wins over shorter quote suffixes.
_QUOTES: tuple[str, ...] = (
    "USDT",
    "USDC",
    "FDUSD",
    "TUSD",
    "BUSD",
    "DAI",
    "BTC",
    "ETH",
    "EUR",
    "TRY",
    "BRL",
)

_SEPARATORS_RE = re.compile(r"[\s/_\-.]+")


def normalize_crypto_symbol(symbol: str) -> str:
    """Return a canonical ``BASEQUOTE`` pair (e.g. ``btc/usdt`` → ``BTCUSDT``).

    - ``-``/``/``/``_``/spaces are removed.
    - ``.P`` and ``-SWAP``/``PERP`` suffixes are dropped (spot is used).
    - A bare base asset gets ``USDT`` appended (``BTC`` → ``BTCUSDT``).
    """
    raw = str(symbol or "").strip().upper()
    if not raw:
        return ""
    raw = raw.replace(".P", "").replace(".PERP", "").replace(".SWAP", "")
    s = _SEPARATORS_RE.sub("", raw)
    s = re.sub(r"(PERP|SWAP)$", "", s)
    if not s:
        return ""
    # Stablecoins/fiat alone are quotes, not a tradable pair (BTC/ETH are
    # legitimate base assets and are handled by the append-USDT branch).
    if s in ("USDT", "USDC", "FDUSD", "TUSD", "BUSD", "DAI", "EUR", "TRY", "BRL"):
        return ""
    if not any(s.endswith(q) and len(s) > len(q) for q in _QUOTES):
        s = f"{s}USDT"
    return s


def split_crypto_symbol(symbol: str) -> tuple[str, str]:
    """Split a canonical pair into ``(base, quote)``; empty strings if invalid."""
    s = normalize_crypto_symbol(symbol)
    for quote in sorted(_QUOTES, key=len, reverse=True):
        if s.endswith(quote) and len(s) > len(quote):
            return s[: -len(quote)], quote
    return "", ""


def is_valid_crypto_symbol(symbol: str) -> bool:
    base, quote = split_crypto_symbol(symbol)
    return len(base) >= 2 and quote in _QUOTES


def is_partial_crypto_symbol_input(symbol: str) -> bool:
    """True while the editable combo still holds a fragment (debounce helper)."""
    s = normalize_crypto_symbol(symbol)
    if not s:
        return True
    if not any(s.endswith(q) for q in _QUOTES):
        return True
    return not is_valid_crypto_symbol(s)


def migrate_general_crypto_defaults(general: dict) -> None:
    """In-place migration of old gold/MT5/TradingView settings to crypto defaults."""
    kind = str(general.get("last_data_source", "binance")).strip().lower()
    if kind not in ("binance", "okx"):
        kind = "binance"
    general["last_data_source"] = kind

    sym = normalize_crypto_symbol(str(general.get("last_symbol", "")))
    # Old installs defaulted to XAUUSDm / XAUUSD — replace with BTC.
    if not sym or sym.startswith(("XAU", "GOLD")) or not is_valid_crypto_symbol(sym):
        sym = CRYPTO_DEFAULT_SYMBOL
    general["last_symbol"] = sym

    tf = str(general.get("last_timeframe", "")).strip()
    general["last_timeframe"] = tf if tf in CRYPTO_TIMEFRAMES else CRYPTO_DEFAULT_TIMEFRAME

    # Removed together with the TradingView data source.
    general.pop("last_tradingview_exchange", None)
