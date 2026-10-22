# Daily cron

GitHub Actions workflow `Scheduled Cron Jobs` runs `ev-charging-growth --months 5 --metals-etf PPLT` daily at 12:00 UTC and commits `data.csv` to the default branch.

## Sub-features

- `cron-schedule` triggers on `0 12 * * *` and `workflow_dispatch`.
- `cron-commit` commits `chore: update data.csv` when the CSV changed.

## How to get to it (user POV)

- GitHub → Actions → `Scheduled Cron Jobs`.

## Driving it with agentctl

Preconditions:

- None locally. This feature is observed, not driven.

- **Observe.** Run `gh run list -R feraranas/simple-ai-agent --workflow cron.yaml --limit 5`. Read-only; recent runs and their conclusions are listed.
- **Effect.** Run `git log --oneline -5 -- data.csv` after `git fetch`. The last commit date shows the last successful run.

## Gotchas

- Never run `gh workflow run` for verification. It spends real API quota and pushes to main.
