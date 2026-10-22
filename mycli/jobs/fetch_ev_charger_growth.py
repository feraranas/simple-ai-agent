from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import List
import httpx

from settings import settings


def _month_labels(months: int, now_utc: datetime) -> List[str]:
    return [(now_utc - timedelta(days=30 * i)).strftime("%Y-%m") for i in reversed(range(months))]


async def fetch_ev_charger_growth(
    months: int,
    max_results: int
) -> List[float]:
    '''Fetch monthly EV charger creation counts from Open Charge Map (real API calls)'''
    base_url = "https://api.openchargemap.io/v3/poi"
    days_ago = months * 30
    since_date = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            base_url,
            params = {
                "key": settings.OPENCHARGEMAP_API_KEY,
                "countryCode": "GB",
                "modifiedsince": since_date,
                "maxresults": max_results,
                "compact": "true",
                "verbose": "false"
            },
            timeout = 20.0
        )
        response.raise_for_status()
        data = response.json()

    monthly_counts = defaultdict(int)
    now_utc = datetime.now(timezone.utc)
    cutoff_dt = now_utc - timedelta(days=days_ago)

    for poi in data:
        created_str = poi.get("DateCreated")
        if created_str:
            try:
                created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                if created_dt >= cutoff_dt:
                    monthly_counts[created_dt.strftime("%Y-%m")] += 1
            except ValueError:
                continue

    return [float(monthly_counts.get(label, 0)) for label in _month_labels(months, now_utc)]


async def fetch_ev_charger_growth_ind(
    months: int
) -> List[float]:
    '''CLI preview of fetch_ev_charger_growth: first 20 POIs, with per-month output'''
    counts_list = await fetch_ev_charger_growth(months, max_results=20)
    labels = _month_labels(months, datetime.now(timezone.utc))
    for i, month_label in zip(reversed(range(months)), labels):
        print(month_label)
        print(f"Month: {i}, Month Label: {month_label}")

    print(f"Counts List: {counts_list}")
    return counts_list
