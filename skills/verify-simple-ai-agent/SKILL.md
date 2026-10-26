---
name: verify-simple-ai-agent
description: Drive the simple-ai-agent Typer CLI (`python main.py fetch-ev-charger-growth | fetch-etf-metal-prices | ev-charging-growth`) fully offline, with an httpx mock boundary for Open Charge Map and Marketstack, dummy keys and a scratch data.csv. Use when you must prove CLI behavior of simple-ai-agent without spending API quota.
---

# Verify simple-ai-agent

The user surface is a Typer CLI (`main.py`) run by hand or by the daily GitHub Actions cron (`.github/workflows/cron.yaml`). Every command calls paid or keyed external APIs (Open Charge Map, Marketstack, OpenAI gpt-4o), so verification runs behind an offline boundary. OpenAI is refused by default. A scripted fake model is available on request (`AGENT_VERIFY_FAKE_LLM=1`). All driving goes through `scripts/agentctl`, which resolves its own real path (works from `skills/`, `.cursor/skills/` or `.claude/skills/`).

## Launch

```bash
export RUN_ID=$(date +%s)   # isolates state in /tmp/verify-saa-$RUN_ID
skills/verify-simple-ai-agent/scripts/agentctl launch
```

Creates a venv in `$STATE/venv` and installs `requirements.txt` (about 15 s). Ready when it prints `READY state=... python=...`. Short-lived CLI: there is no server to keep alive.

## Doctor

```bash
skills/verify-simple-ai-agent/scripts/agentctl doctor
```

Read-only. All lines `OK`: venv exists, `typer`/`pydantic_ai`/`httpx` import, offline shim present, `main.py --help` lists the commands. On 2026-10-26 the first doctor right after `launch` showed one `FAIL CLI help lists commands`. `agentctl cli -- --help` worked, and 17 later tries passed, so the cause is unknown. Rerun doctor once before calling it broken.

Offline pre-checks (no network): `env -i HOME=$HOME PATH=$STATE/venv/bin:/usr/bin:/bin $STATE/venv/bin/python -m unittest discover tests` from the repo root. Expect `Ran 10 tests ... OK`. Leave the API keys unset: `tests/test_fetchers.py` uses `setdefault` and asserts the key is `test-dummy`.

## Drive

- Any command: `agentctl cli -- <main.py args>`. It runs in a clean env (`env -i`) with dummy `OPENCHARGEMAP_API_KEY`/`MARKETSTACK_API_KEY`/`OPENAI_API_KEY`, `STORAGE_FILE_PATH=$STATE/data.csv`, and `PYTHONPATH=scripts/offline` so `sitecustomize.py` gives every httpx client a `MockTransport`.
- The mock answers `api.openchargemap.io/v3/poi` (POIs: 2 created this month, 4 one month ago, ... 10 four months ago) and `api.marketstack.com/v2/eod` (100 daily closes 100.0 → 149.5; symbol `VERIFY-EMPTY` gets `{"data": []}`). Any other host gets HTTP 599 and is logged.
- `api.openai.com/v1/chat/completions` gets 599 too, unless `AGENT_VERIFY_FAKE_LLM=1` is set (agentctl passes it and `AGENT_VERIFY_FAKE_LLM_CORRELATION` through `env -i`). Then a scripted fake model answers: turn 1 calls both fetch tools; turn 2 returns `final_result` with the Pearson correlation of the tool results (fixture data gives `-1.0`) or the override value. The real agent, tools, output validator, panel and CSV append all run. Only the model is fake.
- Journeys (each checks the exit code, an expected output line, an unchanged repo `data.csv` and no 599):
  - `fetch-ev-charger-growth`: exit 0, `Counts List: [10.0, 8.0, 6.0, 4.0, 2.0]`.
  - `fetch-etf-metal-prices`: exit 0.
  - `etf-empty`: exit 1, `No data found for symbol VERIFY-EMPTY`.
  - `agent-skip-today`: seeds a row with today's UTC date. Exit 0, `already fetched today`, empty network log.
  - `agent-fake-llm`: empty scratch CSV. Exit 0, `Correlation: -1.000`, exactly one appended row that passes `scripts/check_data_csv.py`.
- Recipes: [features/README.md](features/README.md).

Isolation: separate `RUN_ID`s share nothing; the repo's tracked `data.csv` is never written.

## Evidence

Per journey in `skills/verify-simple-ai-agent/evidence/$RUN_ID/<journey>/`: `command.txt`, `stdout.txt`, `stderr.txt`, `exit-code.txt`, `network.jsonl.txt` (every outbound request with keys redacted, the mock status, and `fake_llm` turn and tool calls for the fake model), `data-csv-unchanged.txt` (sha of repo `data.csv` before/after), `scratch-data.csv` when the run left one, and `check-data-csv.txt` for `agent-fake-llm`.

Proof standards: drive `main.py` the way a user does. The mock sits only at the HTTP boundary; the CLI's own parsing and counting run for real. Check the network log: a 599 line means the code reached a host the shim does not serve, and the journey fails. The mock skips real API auth, rate limits and real response shapes. The fake model skips real OpenAI: auth, model reasoning, and whether gpt-4o actually calls the tools and computes a sane correlation. Those stay unverified.

Committed reference proof: `evidence/final/`.

## Cleanup

```bash
skills/verify-simple-ai-agent/scripts/agentctl cleanup
```

Removes only `/tmp/verify-saa-$RUN_ID` (venv, scratch CSV, net log). Evidence is kept.

## Helpers

- `scripts/agentctl launch | doctor | cli -- <args> | journey <name> | cleanup` (env `RUN_ID`, optional `AGENT_VERIFY_STATE`, `AGENT_VERIFY_EVIDENCE`; for `cli`, optional `AGENT_VERIFY_FAKE_LLM=1` and `AGENT_VERIFY_FAKE_LLM_CORRELATION`).
- `scripts/offline/sitecustomize.py`: verification-only network boundary and opt-in fake model, loaded only through `agentctl cli`.

## Maintenance

Use `/maintain-verification-skill` to keep `features/` in step with the CLI.
