"""Tests for public gptprof Telegram callbacks."""

import json
import sys
from unittest.mock import MagicMock


import pytest


def _ensure_telegram_mock():
    if "telegram" in sys.modules and hasattr(sys.modules["telegram"], "__file__"):
        return

    mod = MagicMock()
    mod.ext.ContextTypes.DEFAULT_TYPE = type(None)
    mod.constants.ParseMode.MARKDOWN = "Markdown"
    mod.constants.ParseMode.MARKDOWN_V2 = "MarkdownV2"
    mod.constants.ParseMode.HTML = "HTML"
    mod.constants.ChatType.PRIVATE = "private"
    mod.constants.ChatType.GROUP = "group"
    mod.constants.ChatType.SUPERGROUP = "supergroup"
    mod.constants.ChatType.CHANNEL = "channel"
    mod.error.NetworkError = type("NetworkError", (OSError,), {})
    mod.error.TimedOut = type("TimedOut", (OSError,), {})
    mod.error.BadRequest = type("BadRequest", (Exception,), {})

    for name in ("telegram", "telegram.ext", "telegram.constants", "telegram.request"):
        sys.modules.setdefault(name, mod)
    sys.modules.setdefault("telegram.error", mod.error)


_ensure_telegram_mock()

from gateway.config import PlatformConfig
from plugins.platforms.telegram.adapter import TelegramAdapter


def _make_adapter():
    adapter = TelegramAdapter(PlatformConfig(enabled=True, token="test-token"))
    adapter._bot = MagicMock()
    adapter._app = MagicMock()
    return adapter


def test_gptprof_switch_profile_updates_auth_and_config(tmp_path, monkeypatch):
    home = tmp_path / "hermes-home"
    profiles = home / "gptprof" / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "profile1.json").write_text(
        json.dumps(
            {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "email": "user@example.com",
                "plan": "Pro",
            }
        ),
        encoding="utf-8",
    )
    (home / "auth.json").write_text("{}\n", encoding="utf-8")
    (home / "config.yaml").write_text("model:\n  default: MiniMax-M2.7\n  provider: minimax\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(home))

    adapter = _make_adapter()
    ok, message = adapter._gptprof_switch_profile("profile1", "gpt-5.5")

    assert ok, message
    auth = json.loads((home / "auth.json").read_text(encoding="utf-8"))
    assert auth["codex"]["profile"] == "profile1"
    assert auth["codex"]["access_token"] == "test-access-token"
    assert auth["providers"]["openai-codex"]["tokens"]["profile"] == "profile1"
    assert auth["credential_pool"]["openai-codex"][0]["source"] == "gptprof:profile1"

    config = (home / "config.yaml").read_text(encoding="utf-8")
    assert "default: gpt-5.5" in config
    assert "provider: openai-codex" in config


def test_gptprof_switch_rejects_missing_profile(tmp_path, monkeypatch):
    home = tmp_path / "hermes-home"
    (home / "gptprof" / "profiles").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))

    adapter = _make_adapter()
    ok, message = adapter._gptprof_switch_profile("missing", "gpt-5.5")

    assert not ok
    assert "missing" in message
