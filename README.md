# Simple AI Agent with 2 tools and an output validator

A Typer CLI that asks a `pydantic-ai` agent (OpenAI `gpt-4o`) to correlate two series over the last few months:

1. New EV charging stations in Great Britain, from Open Charge Map.
2. Closing prices of a metals ETF (gold, platinum and so on), from Marketstack.

The agent calls one tool per series, computes the correlation and returns a recommendation. An output validator clamps the correlation to [-1, 1]. Each result is appended to `data.csv`.

A GitHub Actions cron job runs the analysis every day at 12:00 UTC (6:00 in Mexico City) and commits the new `data.csv` row:

<p align="center" width=250px>
  <img src="https://github.com/feraranas/simple-ai-agent/blob/main/output.png" />
</p>

## API keys

Create a `.env` file in the repository root (it is git-ignored) with these keys:

| Variable | Where to get it |
| --- | --- |
| `OPENCHARGEMAP_API_KEY` | https://openchargemap.org/site/profile/applications |
| `MARKETSTACK_API_KEY` | https://marketstack.com/dashboard |
| `OPENAI_API_KEY` | https://platform.openai.com/settings/ |

All three are required by every command. Set `STORAGE_FILE_PATH` to write results somewhere other than `data.csv`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Run the agent and append the result to `data.csv`:

```bash
python main.py ev-charging-growth --months 5 --metals-etf PPLT
```

The command skips the analysis if `data.csv` already has a row for that ETF today.

Preview what each tool fetches, without the agent and without writing `data.csv`:

```bash
python main.py fetch-ev-charger-growth --months 5
python main.py fetch-etf-metal-prices --months 5 --symbol GLD
```

`fetch-ev-charger-growth` reads only the first 20 stations; the agent tool reads up to 5000.

## Code overview

```text
.github/workflows/cron.yaml          daily analysis and data.csv commit
main.py                              Typer CLI entry point
settings.py                          keys and STORAGE_FILE_PATH (pydantic-settings, .env)
mycli/jobs/ev_charging_growth.py     agent, its two tools, output validator, CSV append
mycli/jobs/fetch_ev_charger_growth.py  standalone Open Charge Map fetch
mycli/jobs/fetch_metal_prices.py     standalone Marketstack fetch
data.csv                             one row per analysis: timestamp, symbol, correlation, recommendation
```
