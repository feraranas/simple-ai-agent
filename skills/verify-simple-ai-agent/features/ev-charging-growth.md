# Correlation agent

Runs a pydantic-ai agent on OpenAI gpt-4o that calls both fetch tools, computes a correlation, clamps it to [-1, 1], prints a Rich panel and appends a row to `data.csv`.

## Sub-features

- `agent-skip-today` prints `Skipping analysis for <ETF> (already fetched today)` when today's row exists.
- `agent-run` prints `Analysis Results for <ETF>` with `Correlation:` and `Recommendation:`.
- `agent-tools` the model calls `fetch_ev_charger_growth` (same fetcher as the CLI but `maxresults=5000`) and `fetch_metals_prices`.
- `agent-clamp` the output validator clamps the correlation to [-1, 1].
- `agent-append` appends `timestamp,symbol,correlation,recommendation` (UTC ISO timestamp) to `STORAGE_FILE_PATH`.

## How to get to it (user POV)

- `python main.py ev-charging-growth --months 5 --metals-etf PPLT`

## Driving it with agentctl

Preconditions:

- Launched, doctor `OK`.

- **Skip path.** `agentctl journey agent-skip-today` seeds `$STATE/data.csv` with today's UTC date (`date -u +%F`) for `PPLT`. Observed 2026-10-26: exit `0`, panel `Skipping analysis for PPLT (already fetched today).`, empty network log.
- **Full run, fake model.** `agentctl journey agent-fake-llm`. Observed 2026-10-26: exit `0`, panel `Analysis Results for PPLT` with `Correlation: -1.000`. The network log shows 4 lines in order: fake turn 1 (`tool_calls: [fetch_ev_charger_growth, fetch_metals_prices]`), Open Charge Map `maxresults=5000`, Marketstack `PPLT`, then fake turn 2 (`final_result`). One row is appended to the scratch CSV, and `check_data_csv.py` reports `OK`.
- **Clamp.** Run `AGENT_VERIFY_FAKE_LLM=1 AGENT_VERIFY_FAKE_LLM_CORRELATION=1.7 agentctl cli -- ev-charging-growth --metals-etf PPLT` on an empty `$STATE/data.csv`. Observed: `Correlation: 1.000`, CSV value `1.0`.
- **Failed run.** Plain `agentctl cli -- ev-charging-growth` without the fake: the shim refuses `api.openai.com` (3 POSTs, the OpenAI client's retries). The run ends with `ModelHTTPError: status_code: 599`, **exit `1`**, and no CSV row.
- **Real run.** Never driven: it spends OpenAI, Open Charge Map and Marketstack quota and needs real keys.

## Gotchas

- The fake model is scripted. It proves the tool wiring, validator, panel and CSV append, not what gpt-4o would answer.
- `already_fetched_today` compares in UTC since #2 (`bf61dd5`), matching the UTC row timestamps. Seed skip rows with `date -u +%F`. `tests/test_already_fetched_today.py` covers the UTC-6 evening case offline.
- A failed agent run exits non-zero (`1` observed on 2026-10-26). The earlier note that it exits `0` no longer holds.
