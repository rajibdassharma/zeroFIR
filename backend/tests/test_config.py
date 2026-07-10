"""Day-one hardening: Settings must refuse to instantiate if
JWT_SECRET is missing / default / <32 chars."""
import importlib
import sys

import pytest


def _reload_config_with_env(monkeypatch, **env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("config", None)
    return importlib.import_module("config")


def test_default_secret_raises(monkeypatch):
    with pytest.raises(RuntimeError, match="placeholder default"):
        _reload_config_with_env(
            monkeypatch,
            ZFIR_JWT_SECRET="REPLACE-ME-WITH-64-CHAR-HEX",
        )


def test_short_secret_raises(monkeypatch):
    with pytest.raises(RuntimeError, match="too short"):
        _reload_config_with_env(monkeypatch, ZFIR_JWT_SECRET="tooshort")


def test_valid_secret_boots(monkeypatch):
    config = _reload_config_with_env(monkeypatch, ZFIR_JWT_SECRET="x" * 64)
    assert config.settings.JWT_SECRET == "x" * 64
