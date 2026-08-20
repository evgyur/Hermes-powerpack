# Hermes Powerpack Generation 2

Generation 2 is the workshop distribution of Hermes Agent rebuilt on the exact official upstream base `46c0c6ec42a75611971b725954526df22b0761ef` and hardened for long-running Telegram/VPS use.

## What changed

Generation 2 keeps the public workshop skills and adds a reviewed runtime-safety layer:

- **Fail-closed restart recovery.** If Hermes cannot prove whether an interrupted tool call completed, it does not silently replay the action.
- **Empty-history safety.** Missing durable tool history is treated as unavailable evidence, not as proof that retrying is safe.
- **Scope-owner lock.** Reliability, autonomy, skills, and worker tools cannot silently replace the task or runtime the user assigned.
- **Startup provenance.** Restart continuations retain explicit startup/recovery context instead of being mistaken for ordinary user turns.
- **Long-session compression fix.** Idle compaction cannot immediately trigger a second preflight compaction against the same transcript.
- **Multiplex profile safety.** Automatic and manual compression preserve the active profile context across executor threads, so credentials cannot be borrowed from another profile.
- **Conservative routing by default.** Experimental lean routing is not enabled automatically.

## Install

```bash
git clone https://github.com/evgyur/Hermes-powerpack.git
cd Hermes-powerpack
bash scripts/install-powerpack.sh
hermes setup
hermes doctor
```

## Upgrade an existing workshop installation

Run from a normal shell outside the gateway process:

```bash
cd Hermes-powerpack
git pull --ff-only origin main
bash scripts/install-powerpack.sh
hermes doctor
```

If a Hermes gateway is already running, restart it from that external shell so the new Python process loads the updated code.

## Focused Generation 2 verification

```bash
python -m pytest -q \
  tests/gateway/test_startup_tool_outcome_correlation.py \
  tests/gateway/test_restart_resume_pending.py \
  tests/agent/test_system_prompt.py \
  tests/agent/test_system_prompt_restore.py \
  tests/agent/test_idle_compaction_lock_and_guards.py \
  tests/gateway/test_session_hygiene.py \
  tests/gateway/test_compress_command.py
```

## Public provenance

| Layer | Source identity | Public port |
|---|---|---|
| Official Hermes base | `46c0c6ec42a75611971b725954526df22b0761ef` | merge `cba8195326e4ee16cd793a6d699d0101d198679e` |
| Scope/startup policy | `70117369d882f5ec350feb9ee2a46f87197e22a9` | `1e8cacedf4` |
| Ambiguous tool replay guard | `5861a12ede44e0061f92f72d16f902ca74d9fa31` | `0bfe3fbfd6` |
| Empty-history fail-closed fix | `35df2852ea2f7e7ab16737c32b84a6132ec92400` | `7318757f46` |
| Duplicate turn-start compaction fix | `d7e149edd18fe890466bc735480e352f05b4fa33` | `21fd75cfad` |
| Compression profile-scope fix | `336b247a85c8bcc17ee01ea25f12f7b471e59cf7` | `5afe585af5` |

The source identities above are code provenance only. This public repository does not include private organization infrastructure, conversations, credentials, account data, private skills, local runtime state, or production routing configuration.
