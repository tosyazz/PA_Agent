"""Tests for crypto pair normalization and settings migration."""
from __future__ import annotations

from pa_agent.data.market_defaults import (
    CRYPTO_DEFAULT_SYMBOL,
    is_valid_crypto_symbol,
    migrate_general_crypto_defaults,
    normalize_crypto_symbol,
    split_crypto_symbol,
)


def test_normalize_common_inputs():
    assert normalize_crypto_symbol("btc/usdt") == "BTCUSDT"
    assert normalize_crypto_symbol("BTC-USDT") == "BTCUSDT"
    assert normalize_crypto_symbol("BTC_USDT") == "BTCUSDT"
    assert normalize_crypto_symbol("BTCUSDT.P") == "BTCUSDT"
    assert normalize_crypto_symbol("BTC-USDT-SWAP") == "BTCUSDT"
    assert normalize_crypto_symbol("ETH") == "ETHUSDT"
    assert normalize_crypto_symbol("BTC") == "BTCUSDT"
    assert normalize_crypto_symbol("") == ""


def test_normalize_rejects_bare_quote():
    assert normalize_crypto_symbol("USDT") == ""
    assert normalize_crypto_symbol("USDC") == ""


def test_split_and_validate():
    assert split_crypto_symbol("BTCUSDT") == ("BTC", "USDT")
    assert split_crypto_symbol("ETHBTC") == ("ETH", "BTC")
    assert split_crypto_symbol("SOL-USDC") == ("SOL", "USDC")
    assert is_valid_crypto_symbol("BTCUSDT")
    assert not is_valid_crypto_symbol("USDT")
    assert not is_valid_crypto_symbol("")


def test_migrate_old_mt5_tradingview_settings():
    general = {
        "last_data_source": "tradingview",
        "last_symbol": "XAUUSDm",
        "last_timeframe": "15m",
        "last_tradingview_exchange": "OANDA",
    }
    migrate_general_crypto_defaults(general)
    assert general["last_data_source"] == "binance"
    assert general["last_symbol"] == CRYPTO_DEFAULT_SYMBOL
    assert general["last_timeframe"] == "1h"
    assert "last_tradingview_exchange" not in general


def test_migrate_non_1h_timeframes_to_1h():
    for old_tf in ("1m", "5m", "15m", "30m", "4h", "1d", "1w"):
        general = {"last_timeframe": old_tf}
        migrate_general_crypto_defaults(general)
        assert general["last_timeframe"] == "1h"


def test_migrate_preserves_valid_crypto_choice():
    general = {
        "last_data_source": "okx",
        "last_symbol": "ETHUSDT",
        "last_timeframe": "1h",
    }
    migrate_general_crypto_defaults(general)
    assert general["last_data_source"] == "okx"
    assert general["last_symbol"] == "ETHUSDT"
    assert general["last_timeframe"] == "1h"
