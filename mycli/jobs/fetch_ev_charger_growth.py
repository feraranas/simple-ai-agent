from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import List
import httpx

from settings import settings

async def fetch_ev_charger_growth_ind(
    months: int
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
                "maxresults": 20,
                "compact": "true",
                "verbose": "false"
            },
            timeout = 20.0
        )
        response.raise_for_status()
        data = response.json()

    monthly_counts = defaultdict(int)                # defaultdict(<class 'int'>, {})
    now_utc = datetime.now(timezone.utc)             # 2025-04-20 18:53:07.717510+00:00 or as: datetime.datetime(2025, 4, 21, 3, 57, 36, 332387, tzinfo=datetime.timezone.utc)
    timedelta_days_ago = timedelta(days = days_ago)  # 180 days, 0:00:00 or as: datetime.timedelta(days=180)
    cutoff_dt = now_utc - timedelta_days_ago         # 2024-10-22 18:57:02.558334+00:00 or as: datetime.datetime(2024, 10, 23, 3, 57, 36, 332387, tzinfo=datetime.timezone.utc)

    for poi in data:
        created_str = poi.get("DateCreated")         # "2025-04-20T19:02:00Z"
        if created_str:
            try:
                created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00")) # datetime.datetime(2025, 4, 20, 19, 2, tzinfo=datetime.timezone.utc)
                if created_dt >= cutoff_dt:
                    month_key = created_dt.strftime("%Y-%m")    # "2025-04"
                    monthly_counts[month_key] += 1              # defaultdict(<class 'int'>, {'2025-04': 5})
            except ValueError:
                continue

    # Create a list of monthly counts in order
    counts_list = []
    for i in reversed(range(months)):
        month_label = (now_utc - timedelta(days=30 * i)).strftime("%Y-%m")
        print(month_label)
        counts_list.append(float(monthly_counts.get(month_label, 0)))
        print(f"Month: {i}, Month Label: {month_label}")

    print(f"Counts List: {counts_list}") # [0.0, 0.0, 0.0, 13.0, 7.0]
    return counts_list
