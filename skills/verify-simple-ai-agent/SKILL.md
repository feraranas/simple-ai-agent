---
name: verify-simple-ai-agent
description: Drive the simple-ai-agent Typer CLI (`python main.py fetch-ev-charger-growth | fetch-etf-metal-prices | ev-charging-growth`) fully offline, with an httpx mock boundary for Open Charge Map and Marketstack, dummy keys and a scratch data.csv. Use when you must prove CLI behavior of simple-ai-agent without spending API quota.
---

# Verify simple-ai-agent

The user surface is a Typer CLI (`main.py`) run by hand or by the daily GitHub Actions cron (`.github/workflows/cron.yaml`). Every command calls paid or keyed external APIs (Open Charge Map, Marketstack, OpenAI gpt-4o), so verification runs behind an offline boundary. All driving goes through `scripts/agentctl`, which resolves its own real path (works from `skills/`, `.cursor/skills/` or `.claude/skills/`).

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

Read-only. All lines `OK`: venv exists, `typer`/`pydantic_ai`/`httpx` import, offline shim present, `main.py --help` lists the commands.

## Drive

- Any command: `agentctl cli -- <main.py args>`. It runs in a clean env (`env -i`) with dummy `OPENCHARGEMAP_API_KEY`/`MARKETSTACK_API_KEY`/`OPENAI_API_KEY`, `STORAGE_FILE_PATH=$STATE/data.csv`, and `PYTHONPATH=scripts/offline` so `sitecustomize.py` gives every httpx client a `MockTransport`.
- The mock answers `api.openchargemap.io/v3/poi` (POIs: 2 created this month, 4 one month ago, ... 10 four months ago) and `api.marketstack.com/v2/eod` (100 daily closes 100.0 → 149.5). Any other host gets HTTP 599 and is logged.
- Journeys: `agentctl journey fetch-ev-charger-growth` and `agentctl journey fetch-etf-metal-prices`.
- Recipes: [features/README.md](features/README.md).

Isolation: separate `RUN_ID`s share nothing; the repo's tracked `data.csv` is never written.

## Evidence

Per journey in `skills/verify-simple-ai-agent/evidence/$RUN_ID/<journey>/`: `command.txt`, `stdout.txt`, `stderr.txt`, `exit-code.txt`, `network.jsonl.txt` (every outbound request with keys redacted, and the mock status), `data-csv-unchanged.txt` (sha of repo `data.csv` before/after).

Proof standards: drive `main.py` the way a user does. The mock sits only at the HTTP boundary; the CLI's own parsing and counting run for real. Check the network log: a 599 line means the code reached a host the shim does not serve, and the journey fails. The mock skips real API auth, rate limits, real response shapes, and OpenAI. Those stay unverified.

Committed reference proof: `evidence/final/`.

## Cleanup

```bash
skills/verify-simple-ai-agent/scripts/agentctl cleanup
```

Removes only `/tmp/verify-saa-$RUN_ID` (venv, scratch CSV, net log). Evidence is kept.

## Helpers

- `scripts/agentctl launch | doctor | cli -- <args> | journey <name> | cleanup` (env `RUN_ID`, optional `AGENT_VERIFY_STATE`, `AGENT_VERIFY_EVIDENCE`).
- `scripts/offline/sitecustomize.py`: verification-only network boundary, loaded only through `agentctl cli`.

## Maintenance

Use `/maintain-verification-skill` to keep `features/` in step with the CLI.
