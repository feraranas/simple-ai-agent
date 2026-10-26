# Daily cron

GitHub Actions workflow `Scheduled Cron Jobs` runs `ev-charging-growth --months 5 --metals-etf PPLT` daily at 12:00 UTC and commits `data.csv` to the default branch.

## Sub-features

- `cron-schedule` triggers on `0 12 * * *` and `workflow_dispatch`.
- `cron-check` runs `python scripts/check_data_csv.py data.csv` before committing. A malformed row fails the job.
- `cron-commit` commits `chore: update data.csv` when the CSV changed.

## How to get to it (user POV)

- GitHub → Actions → `Scheduled Cron Jobs`.

## Driving it with agentctl

Preconditions:

- Schedule and commit: none locally. They are observed, not driven.
- `cron-check`: a launched venv.

- **Observe.** Run `gh run list -R feraranas/simple-ai-agent --workflow cron.yaml --limit 5`. Read-only; recent runs and their conclusions are listed.
- **Effect.** Run `git log --oneline -5 -- data.csv` after `git fetch`. The last commit date shows the last successful run.
- **Check step (offline).** From the repo root, run `$STATE/venv/bin/python scripts/check_data_csv.py data.csv`. It is read-only. Observed 2026-10-26: `checked 40 rows in data.csv: OK`, exit 0. A scratch CSV with a bad timestamp, a correlation of 2.5 and an empty recommendation gives 3 problems and exit 1.
- Observed 2026-10-26: the workflow is `active` and the repo secrets exist, but `gh run list` returns no runs. The last `chore: update data.csv` commit is `2d048ee` (2025-06-01 12:19 UTC). Report this as an operational gap. Do not trigger a run.

## Gotchas

- Never run `gh workflow run` for verification. It spends real API quota and pushes to main.
