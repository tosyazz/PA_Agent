"""Construct crypto :class:`DataSource` implementations by kind id."""
from __future__ import annotations

from pa_agent.config.settings import DataSourceKind
from pa_agent.data.base import DataSource
from pa_agent.data.market_defaults import CRYPTO_DEFAULT_SYMBOL

#: Data sources offered in the UI. Only crypto exchanges are supported.
DATA_SOURCE_CHOICES: tuple[tuple[DataSourceKind, str], ...] = (
    ("binance", "币安 Binance"),
    ("okx", "OKX"),
)

_DEFAULT_SYMBOLS: dict[DataSourceKind, str] = {
    "binance": CRYPTO_DEFAULT_SYMBOL,
    "okx": CRYPTO_DEFAULT_SYMBOL,
}


def normalize_data_source_kind(kind: str | None) -> DataSourceKind:
    """Return a supported crypto exchange kind, defaulting to Binance."""
    if str(kind or "").strip().lower() == "okx":
        return "okx"
    return "binance"


def data_source_label(kind: str | None) -> str:
    """Human-readable label for *kind* (e.g. ``币安 Binance``)."""
    normalized = normalize_data_source_kind(kind)
    for key, label in DATA_SOURCE_CHOICES:
        if key == normalized:
            return label
    return "币安 Binance"


def default_symbol_for_kind(kind: str | None) -> str:
    return _DEFAULT_SYMBOLS[normalize_data_source_kind(kind)]


def create_data_source(kind: str | None) -> DataSource:
    """Instantiate a fresh crypto data source for *kind* (not connected)."""
    normalized = normalize_data_source_kind(kind)
    if normalized == "okx":
        from pa_agent.data.okx_source import OkxSource

        return OkxSource()
    from pa_agent.data.binance_source import BinanceSource

    return BinanceSource()
