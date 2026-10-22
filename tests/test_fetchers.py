"""Behavior of the two data fetchers behind the CLI and the agent tools.

The HTTP APIs are replaced with httpx.MockTransport; everything after the
response (filtering, monthly bucketing, sampling, padding) runs for real.
Run: python -m unittest discover tests
"""
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import httpx

for key in ("OPENCHARGEMAP_API_KEY", "MARKETSTACK_API_KEY", "OPENAI_API_KEY"):
    os.environ.setdefault(key, "test-dummy")

from mycli.jobs.fetch_ev_charger_growth import fetch_ev_charger_growth_ind  # noqa: E402
from mycli.jobs.fetch_metal_prices import fetch_metals_prices_ind  # noqa: E402

RealAsyncClient = httpx.AsyncClient


def serve(payload):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=payload)

    def client(*args, **kwargs):
        return RealAsyncClient(transport=httpx.MockTransport(handler))

    return mock.patch("httpx.AsyncClient", client), requests


def iso_days_ago(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")


class EvChargerGrowthTest(unittest.IsolatedAsyncioTestCase):
    async def test_counts_chargers_per_month_oldest_first(self):
        pois = [{"DateCreated": iso_days_ago(0)}] * 3 + [{"DateCreated": iso_days_ago(30)}] * 2
        patch, _ = serve(pois)
        with patch, mock.patch("builtins.print"):
            counts = await fetch_ev_charger_growth_ind(3)
        self.assertEqual(counts, [0.0, 2.0, 3.0])

    async def test_skips_pois_outside_window_or_without_a_valid_date(self):
        pois = [
            {"DateCreated": iso_days_ago(0)},
            {"DateCreated": iso_days_ago(400)},
            {"DateCreated": "not-a-date"},
            {"DateCreated": None},
            {},
        ]
        patch, _ = serve(pois)
        with patch, mock.patch("builtins.print"):
            counts = await fetch_ev_charger_growth_ind(2)
        self.assertEqual(counts, [0.0, 1.0])

    async def test_queries_great_britain_with_the_api_key(self):
        patch, requests = serve([])
        with patch, mock.patch("builtins.print"):
            await fetch_ev_charger_growth_ind(1)
        params = requests[0].url.params
        self.assertEqual(requests[0].url.host, "api.openchargemap.io")
        self.assertEqual(params["countryCode"], "GB")
        self.assertEqual(params["key"], "test-dummy")


class MetalsPricesTest(unittest.IsolatedAsyncioTestCase):
    async def test_samples_one_close_per_month_from_daily_data(self):
        daily = [{"close": float(day)} for day in range(10)]
        patch, _ = serve({"data": daily})
        with patch:
            prices = await fetch_metals_prices_ind("GLD", 5)
        self.assertEqual(prices, [0.0, 2.0, 4.0, 6.0, 8.0])

    async def test_pads_with_last_close_when_history_is_short(self):
        patch, _ = serve({"data": [{"close": 1.0}, {"close": 2.0}]})
        with patch:
            prices = await fetch_metals_prices_ind("GLD", 4)
        self.assertEqual(prices, [1.0, 2.0, 2.0, 2.0])

    async def test_raises_when_symbol_has_no_data(self):
        patch, _ = serve({"data": []})
        with patch, self.assertRaisesRegex(ValueError, "No data found for symbol NOPE"):
            await fetch_metals_prices_ind("NOPE", 5)


if __name__ == "__main__":
    unittest.main()
