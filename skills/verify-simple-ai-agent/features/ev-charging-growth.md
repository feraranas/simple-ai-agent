# Correlation agent

Runs a pydantic-ai agent on OpenAI gpt-4o that calls both fetch tools, computes a correlation, clamps it to [-1, 1], prints a Rich panel and appends a row to `data.csv`.

## Sub-features

- `agent-skip-today` prints `Skipping analysis for <ETF> (already fetched today)` when today's row exists.
- `agent-run` prints `Analysis Results for <ETF>` with `Correlation:` and `Recommendation:`.
- `agent-append` appends `timestamp,symbol,correlation,recommendation` to `STORAGE_FILE_PATH`.

## How to get to it (user POV)

- `python main.py ev-charging-growth --months 5 --metals-etf PPLT`

## Driving it with agentctl

Preconditions:

- Launched. For `agent-skip-today`, seed `$STATE/data.csv` with a row dated today (UTC) for `PPLT`.

- **Skip path (offline).** Run `printf '%sT00:00:00+00:00,PPLT,0,x\n' "$(date +%F)" > $STATE/data.csv` (local date, see Gotchas) then `agentctl cli -- ev-charging-growth --metals-etf PPLT`. Exit `0`; stdout has `already fetched today`; `network.jsonl.txt` is empty.
- **Full run.** Not drivable offline: the shim refuses `api.openai.com` (599). A real run spends OpenAI, Open Charge Map and Marketstack quota and needs real keys.

## Gotchas

- `agent-skip-today` observed 2026-10-21: exit `0`, panel `Skipping analysis for PPLT (already fetched today).`, empty network log. Not captured as committed evidence.
- Not proved. The full agent run is unverified; only a fake OpenAI server (`OPENAI_BASE_URL`) could make it offline, and none exists yet.
- `already_fetched_today` compares the row date to local `date.today()`, but rows are written in UTC. Observed: with box TZ UTC-6 in the evening, a row stamped with today's UTC date did not match, and the agent went on to call `api.openai.com` (blocked by the shim: `ModelHTTPError: status_code: 599`, still exit `0`).
- A failed agent run still exits `0`. Check stdout for `ModelHTTPError`, not the exit code.
