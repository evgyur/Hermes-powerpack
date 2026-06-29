from __future__ import annotations

from types import SimpleNamespace

from agent.agent_init import _should_print_codex_gpt55_autoraise_notice


def test_codex_gpt55_autoraise_notice_prints_for_cli_startup() -> None:
    assert _should_print_codex_gpt55_autoraise_notice(
        SimpleNamespace(quiet_mode=False, platform="cli")
    )


def test_codex_gpt55_autoraise_notice_prints_for_legacy_no_platform_cli() -> None:
    assert _should_print_codex_gpt55_autoraise_notice(
        SimpleNamespace(quiet_mode=False, platform=None)
    )


def test_codex_gpt55_autoraise_notice_does_not_print_for_gateway_platforms() -> None:
    assert not _should_print_codex_gpt55_autoraise_notice(
        SimpleNamespace(quiet_mode=False, platform="telegram")
    )


def test_codex_gpt55_autoraise_notice_respects_quiet_mode() -> None:
    assert not _should_print_codex_gpt55_autoraise_notice(
        SimpleNamespace(quiet_mode=True, platform="cli")
    )
