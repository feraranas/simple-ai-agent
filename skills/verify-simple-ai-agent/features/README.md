# simple-ai-agent verification map

This directory is the maintained source for verifying the `main.py` CLI. Read the index, then use the matching feature file.

## Baseline preconditions

- `export RUN_ID=<unique>`, `agentctl launch`, `agentctl doctor` all `OK`.
- Drive only through `agentctl cli --` (offline shim, dummy keys, scratch CSV).

## Proof and skip reporting

- CLI proof = command, stdout, stderr, exit code, plus `network.jsonl.txt` and the `data.csv` hash.
- Real Open Charge Map, Marketstack and OpenAI calls are never made; report them as unverified. A run with `AGENT_VERIFY_FAKE_LLM=1` proves the agent wiring, not the model.

## Features

- [EV charger growth fetch](./fetch-ev-charger-growth.md): `fetch-ev-charger-growth --months N`.
- [ETF metal prices fetch](./fetch-etf-metal-prices.md): `fetch-etf-metal-prices --symbol S --months N`.
- [Correlation agent](./ev-charging-growth.md): `ev-charging-growth`, the full LLM agent that appends to data.csv (offline with the fake model).
- [Daily cron](./daily-cron.md): the GitHub Actions workflow that runs the agent, checks data.csv with `scripts/check_data_csv.py` and commits it.
