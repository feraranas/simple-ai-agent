from datetime import datetime, timedelta, timezone
from typing import List
import httpx

from settings import settings

async def fetch_metals_prices_ind(
    symbol: str,
    months: int
) -> List[float]:
    """Fetch monthly EOD prices for a metals ETF from Marketstack (real API calls)."""
    base_url = "https://api.marketstack.com/v2/eod"
    now_utc = datetime.now(timezone.utc)

    params = {
        "access_key": settings.MARKETSTACK_API_KEY,
        "symbols": symbol,
        "date_from": (now_utc - timedelta(days=months * 30)).strftime("%Y-%m-%d"),
        "date_to": now_utc.strftime("%Y-%m-%d"),
        "limit": 200,
        "sort": "ASC"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(base_url, params=params, timeout=20.0)
        response.raise_for_status()
        payload = response.json()

    if not (daily_data := payload.get("data")):
        raise ValueError(f"No data found for symbol {symbol}")
    
    # We want to pick monthly intervals from daily data
    step = max(1, len(daily_data) // months)
    results = [daily_data[i]["close"] for i in range(0, len(daily_data), step)][:months]

    # If we don't have enough months, pad with last known price
    if results and len(results) < months:
        results += [results[-1]] * (months - len(results))

    return results
