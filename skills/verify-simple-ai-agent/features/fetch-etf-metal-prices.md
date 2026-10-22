# ETF metal prices fetch

Fetches Marketstack end-of-day prices for an ETF symbol over N months and samples one close per month.

## Sub-features

- `etf-request` sends `GET /v2/eod` with `symbols`, `date_from`, `date_to`, `limit=200`, `sort=ASC`.
- `etf-empty` raises `No data found for symbol` when `data` is empty.

## How to get to it (user POV)

- `python main.py fetch-etf-metal-prices --symbol GLD --months 5`

## Driving it with agentctl

Preconditions:

- Launched, doctor `OK`.

- **Fetch.** Run `agentctl journey fetch-etf-metal-prices`. Exit `0`, empty stdout and stderr.
- **Request.** `network.jsonl.txt` has host `api.marketstack.com`, path `/v2/eod`, `symbols: GLD`, a `date_from`..`date_to` window of about 150 days, status 200.

## Gotchas

- The command prints nothing on success (the list is returned, not printed). Exit code and the request log are the only observable proof.
- `etf-empty` is mapped but not proved; the shim always returns data.
