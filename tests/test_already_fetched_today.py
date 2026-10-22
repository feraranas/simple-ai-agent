"""Regression: already_fetched_today must compare in UTC, the zone rows are written in.

Scenario: 2026-10-21 20:30 in America/Mexico_City (UTC-6) == 2026-10-22 02:30 UTC.
A row written earlier that evening is stamped 2026-10-22T02:00:00+00:00.
Run: OPENCHARGEMAP_API_KEY=x MARKETSTACK_API_KEY=x OPENAI_API_KEY=x TZ=America/Mexico_City python -m unittest tests.test_already_fetched_today
"""
import os, tempfile, time, unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

os.environ.setdefault("TZ", "America/Mexico_City")
time.tzset()
for k in ("OPENCHARGEMAP_API_KEY", "MARKETSTACK_API_KEY", "OPENAI_API_KEY"):
    os.environ.setdefault(k, "test-dummy")

from mycli.jobs import ev_charging_growth as job  # noqa: E402

NOW_UTC = datetime(2026, 10, 22, 2, 30, tzinfo=timezone.utc)


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW_UTC if tz is not None else NOW_UTC.astimezone().replace(tzinfo=None)


class FrozenDate(date):
    @classmethod
    def today(cls):
        return NOW_UTC.astimezone().date()  # local date: 2026-10-21 in UTC-6


class AlreadyFetchedTodayTest(unittest.TestCase):
    def check(self, rows):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "data.csv"
            p.write_text("".join(r + "\n" for r in rows))
            with mock.patch.object(job, "datetime", FrozenDateTime), mock.patch.object(job, "date", FrozenDate):
                return job.already_fetched_today(p, "PPLT")

    def test_local_clock_is_utc_minus_6(self):
        self.assertEqual(time.strftime("%Z"), "CST")
        self.assertEqual(FrozenDate.today().isoformat(), "2026-10-21")

    def test_row_written_this_utc_day_counts_in_utc_minus_6_evening(self):
        self.assertTrue(self.check(["2026-10-22T02:00:00+00:00,PPLT,0.1,x"]))

    def test_previous_utc_day_does_not_count(self):
        self.assertFalse(self.check(["2026-10-21T12:20:00+00:00,PPLT,0.1,x"]))

    def test_other_symbol_does_not_count(self):
        self.assertFalse(self.check(["2026-10-22T02:00:00+00:00,GLD,0.1,x"]))


if __name__ == "__main__":
    unittest.main()
