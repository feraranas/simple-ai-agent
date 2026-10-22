"""Check that data.csv only holds well-formed analysis rows.

Each row the cron job appends must be: an ISO-8601 timestamp, an ETF symbol,
a correlation in [-1, 1], and a non-empty recommendation.

Usage: python scripts/check_data_csv.py [path]   (default: data.csv)
Exit code 0 when every row is valid, 1 otherwise.
"""
import csv
import math
import sys
from datetime import datetime
from pathlib import Path


def row_errors(row: list[str]) -> list[str]:
    if len(row) != 4:
        return [f"expected 4 columns, got {len(row)}"]
    timestamp, symbol, correlation, recommendation = row
    errors = []
    try:
        datetime.fromisoformat(timestamp)
    except ValueError:
        errors.append(f"timestamp is not ISO-8601: {timestamp!r}")
    if not symbol.strip():
        errors.append("symbol is empty")
    try:
        value = float(correlation)
        if math.isnan(value) or not -1.0 <= value <= 1.0:
            errors.append(f"correlation outside [-1, 1]: {correlation}")
    except ValueError:
        errors.append(f"correlation is not a number: {correlation!r}")
    if not recommendation.strip():
        errors.append("recommendation is empty")
    return errors


def main(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    bad = 0
    for line, row in enumerate(rows, start=1):
        for error in row_errors(row):
            print(f"{path}:{line}: {error}")
            bad += 1
    print(f"checked {len(rows)} rows in {path}: {'OK' if bad == 0 else f'{bad} problem(s)'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "data.csv")))
