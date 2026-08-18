from datetime import datetime

import pytest

from gateway.run import GatewayRunner, build_resume_recovery_note
from tests.gateway.restart_test_helpers import make_restart_runner, make_restart_source


class HistoryDB:
    def __init__(self, rows):
        self.rows = rows

    def get_messages(self, _session_id):
        return self.rows


def _assistant_call(*, item_id="call_1", call_id=None, name="terminal"):
    call = {"id": item_id, "function": {"name": name, "arguments": "{}"}}
    if call_id is not None:
        call["call_id"] = call_id
    return {"role": "assistant", "content": None, "tool_calls": [call]}


def _tool_result(call_id):
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "tool_name": "terminal",
        "content": "completed",
    }


def test_responses_call_id_wins_over_provider_item_id():
    calls = GatewayRunner._startup_tool_calls_from_message(
        _assistant_call(item_id="fc_123", call_id="call_ABC")
    )
    assert calls == [("call_ABC", "terminal")]


def test_unresolved_tool_call_fails_closed():
    runner, _ = make_restart_runner()
    runner._session_db = HistoryDB([_assistant_call()])
    assert runner._unresolved_startup_tool_call_risk("sid") == (
        "unresolved tool call(s): terminal"
    )


def test_matching_generic_tool_result_allows_resume():
    runner, _ = make_restart_runner()
    runner._session_db = HistoryDB([_assistant_call(), _tool_result("call_1")])
    assert runner._unresolved_startup_tool_call_risk("sid") is None


def test_matching_codex_responses_tool_result_allows_resume():
    runner, _ = make_restart_runner()
    runner._session_db = HistoryDB(
        [
            _assistant_call(item_id="fc_123", call_id="call_ABC"),
            _tool_result("call_ABC"),
        ]
    )
    assert runner._unresolved_startup_tool_call_risk("sid") is None


def test_plain_assistant_checkpoint_bounds_old_ambiguity():
    runner, _ = make_restart_runner()
    runner._session_db = HistoryDB(
        [
            _assistant_call(),
            {"role": "assistant", "content": "done", "tool_calls": None},
        ]
    )
    assert runner._unresolved_startup_tool_call_risk("sid") is None


def test_missing_history_fails_closed():
    runner, _ = make_restart_runner()
    runner._session_db = None
    runner.session_store._db = None
    assert runner._unresolved_startup_tool_call_risk("sid") == "tool history unavailable"


def test_empty_history_fails_closed():
    runner, _ = make_restart_runner()
    runner._session_db = HistoryDB([])
    assert runner._unresolved_startup_tool_call_risk("sid") == "tool history unavailable"


def test_resume_note_requires_reconciliation_before_retry():
    note = build_resume_recovery_note("restart_timeout", "", startup_resume=True)
    assert "UNKNOWN" in note
    assert "reconcile" in note
    assert "proven not to duplicate" in note


@pytest.mark.asyncio
async def test_scheduler_withholds_unresolved_tool_effect_and_alerts_once(monkeypatch):
    runner, adapter = make_restart_runner()
    source = make_restart_source()

    class Entry:
        session_key = "telegram:123456"
        session_id = "sid"
        resume_pending = True
        suspended = False
        origin = source
        resume_reason = "restart_timeout"
        last_resume_marked_at = datetime.now()
        updated_at = datetime.now()

    entry = Entry()
    runner.session_store._entries = {entry.session_key: entry}
    runner._session_db = HistoryDB([_assistant_call(name="terminal")])
    runner._is_session_running = lambda _key: False
    monkeypatch.setattr(
        "gateway.restart_loop_guard.check_and_record",
        lambda *_args, **_kwargs: False,
    )

    assert runner._schedule_resume_pending_sessions() == 0
    await __import__("asyncio").sleep(0)

    assert adapter.sent == [
        "⚠️ Interrupted session was found after gateway startup, but "
        "auto-resume was withheld: ambiguous-tool-outcome: unresolved tool "
        "call(s): terminal.\nSend a new message after reconciling the "
        "external effect."
    ]
    assert entry.resume_pending is True
    assert runner._schedule_resume_pending_sessions() == 0
    await __import__("asyncio").sleep(0)
    assert len(adapter.sent) == 1


@pytest.mark.asyncio
async def test_scheduler_withholds_empty_history_fail_closed(monkeypatch):
    runner, adapter = make_restart_runner()
    source = make_restart_source()

    class Entry:
        session_key = "telegram:123456"
        session_id = "empty-sid"
        resume_pending = True
        suspended = False
        origin = source
        resume_reason = "restart_timeout"
        last_resume_marked_at = datetime.now()
        updated_at = datetime.now()

    entry = Entry()
    runner.session_store._entries = {entry.session_key: entry}
    runner._session_db = HistoryDB([])
    runner._is_session_running = lambda _key: False
    monkeypatch.setattr(
        "gateway.restart_loop_guard.check_and_record",
        lambda *_args, **_kwargs: False,
    )

    assert runner._schedule_resume_pending_sessions() == 0
    await __import__("asyncio").sleep(0)
    assert adapter.sent == [
        "⚠️ Interrupted session was found after gateway startup, but "
        "auto-resume was withheld: ambiguous-tool-outcome: tool history "
        "unavailable.\nSend a new message after reconciling the external "
        "effect."
    ]
    assert entry.resume_pending is True
