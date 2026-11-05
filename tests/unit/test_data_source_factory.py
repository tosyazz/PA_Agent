"""Tests for the crypto-only data source factory and settings defaults."""
from __future__ import annotations

from pa_agent.config.settings import GeneralSettings
from pa_agent.data.binance_source import BinanceSource
from pa_agent.data.factory import (
    DATA_SOURCE_CHOICES,
    create_data_source,
    data_source_label,
    default_symbol_for_kind,
    normalize_data_source_kind,
)
from pa_agent.data.okx_source import OkxSource


def test_ui_choices_are_only_binance_and_okx():
    assert [k for k, _ in DATA_SOURCE_CHOICES] == ["binance", "okx"]
    assert DATA_SOURCE_CHOICES[0][0] == "binance"


def test_normalize_data_source_kind_defaults_to_binance():
    assert normalize_data_source_kind("invalid") == "binance"
    assert normalize_data_source_kind(None) == "binance"
    assert normalize_data_source_kind("mt5") == "binance"
    assert normalize_data_source_kind("tradingview") == "binance"
    assert normalize_data_source_kind("OKX") == "okx"


def test_create_data_source_returns_exchange_adapters():
    assert isinstance(create_data_source("binance"), BinanceSource)
    assert isinstance(create_data_source("okx"), OkxSource)
    # Unknown / removed kinds fall back to Binance.
    assert isinstance(create_data_source("tradingview"), BinanceSource)


def test_labels_and_default_symbols():
    assert data_source_label("binance") == "币安 Binance"
    assert data_source_label("okx") == "OKX"
    assert default_symbol_for_kind("binance") == "BTCUSDT"
    assert default_symbol_for_kind("okx") == "BTCUSDT"


def test_general_settings_default_is_crypto():
    g = GeneralSettings()
    assert g.last_data_source == "binance"
    assert g.last_symbol == "BTCUSDT"
    assert g.last_timeframe == "1h"


def test_only_1h_timeframe_is_supported():
    assert create_data_source("binance").supported_timeframes() == ["1h"]
    assert create_data_source("okx").supported_timeframes() == ["1h"]
