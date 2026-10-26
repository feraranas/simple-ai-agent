# EV charger growth fetch

Fetches Open Charge Map POIs for GB and prints a per-month count of chargers created over the last N months.

## Sub-features

- `ev-request` sends `GET /v3/poi` with `countryCode=GB`, `modifiedsince`, `maxresults=20` (the agent tool shares this fetcher with `maxresults=5000`).
- `ev-bucket` buckets `DateCreated` by `YYYY-MM` and prints, per month, the bare label `YYYY-MM` then `Month: i, Month Label: YYYY-MM`.
- `ev-counts` prints `Counts List: [...]` oldest month first.

## How to get to it (user POV)

- `python main.py fetch-ev-charger-growth --months 5`

## Driving it with agentctl

Preconditions:

- Launched, doctor `OK`.

- **Fetch.** Run `agentctl journey fetch-ev-charger-growth` (= `agentctl cli -- fetch-ev-charger-growth --months 5`). Exit `0`; stdout ends `Counts List: [10.0, 8.0, 6.0, 4.0, 2.0]` with the five month labels ending at the current UTC month.
- **Request.** `network.jsonl.txt` has one line, host `api.openchargemap.io`, path `/v3/poi`, `countryCode: GB`, `maxresults: 20`, status 200.

## Gotchas

- The count list depends on the shim's fixture, not real data. It proves bucketing and ordering only.
- Month labels use 30-day steps in UTC, so near month boundaries two labels can repeat or skip a month.
- The repo's `sample-OpenChargeMap.json` is a single object, not the list the API returns. Do not use it as a fixture.
