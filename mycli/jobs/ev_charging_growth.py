import csv
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import List, Optional
from collections import defaultdict

import httpx
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich.console import Console
from rich.panel import Panel

from settings import settings


console = Console()


class EvChargingGrowthResult(BaseModel):
    '''Result model for EV charging growth analysis.'''
    model_config = ConfigDict(frozen = False)
    
    metals_etf_symbol: str = Field(..., description="Symbol of the analyzed metals ETF")
    correlation: float = Field(..., description="Correlation coefficient between EV growth and metals price")
    recommendation: str = Field(..., description="Analysis-based recommendation")
###
# result = EvChargingGrowthResult(
#    metals_etf_symbol="GLD",
#    correlation=0.72,
#    recommendation="Positive trend—consider a 10% overweight position."
#)
###

def already_fetched_today(csv_path: Path, metals_etf: str) -> bool:
    '''Check if data for the specified ETF has already been fetched today.'''
    today_str = date.today().isoformat()

    if not csv_path.exists():
        return False
    
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            # If the date matches today's date and the symbol matches, we've already stored it.
            if row[0][:10] == today_str and row[1] == metals_etf:
                return True
    
    return False


# --------------------------------------
# 1) Create our Agent and register tools
# --------------------------------------
model = OpenAIModel(
    model_name = "gpt-4o",
    provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY)
)

agent = Agent(
    model,
    deps_type = None,
    result_type = EvChargingGrowthResult,
    system_prompt = """
    You are analyzing EV charging growth rates vs. a metals ETF's monthly prices.
    1. Call the provided tools to fetch real data
    2. Then compute correlation
    3. Return final JSON with (metals_etf_symbol, correlation, recommendation)
    """
)

@agent.tool
async def fetch_ev_charger_growth(
    ctx: RunContext[None],
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
                "maxresults": 5000,
                "compact": "true",
                "verbose": "false"
            },
            timeout = 20.0
        )
        response.raise_for_status()
        data = response.json()

    monthly_counts = defaultdict(int)                # defaultdict(<class 'int'>, {})
    now_utc = datetime.now(timezone.utc)             # 2025-04-20 18:53:07.717510+00:00
    timedelta_days_ago = timedelta(days = days_ago)  # 180 days, 0:00:00
    cutoff_dt = now_utc - timedelta_days_ago         # 2024-10-22 18:57:02.558334+00:00 

    for poi in data:
        created_str = poi.get("DateCreated")
        if created_str:
            try:
                created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                if created_dt >= cutoff_dt:
                    month_key = created_dt.strftime("%Y-%m")
                    # defaultdict(<class 'int'>, {'2025-04': 5})
                    monthly_counts[month_key] += 1
            except ValueError:
                continue

    # Create a list of monthly counts in order
    counts_list = []
    for i in reversed(range(months)):
        month_label = (now_utc - timedelta(days=30 * i)).strftime("%Y-%m")
        counts_list.append(float(monthly_counts.get(month_label, 0)))

    return counts_list


@agent.tool
async def fetch_metals_prices(
    ctx: RunContext[None],
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


@agent.output_validator
def finalize_result(
    ctx: RunContext[None], 
    data: EvChargingGrowthResult
) -> EvChargingGrowthResult:
    """Post-process and ensure correlation is in [-1, 1] range."""
    # For safety, clamp correlation
    data.correlation = max(-1.0, min(1.0, data.correlation))
    return data


# ---------------------------------
# 2) Main function to run the agent
# ---------------------------------
async def run_ev_charging_growth(
    months: int = 5,
    metals_etf: str = "PPLT"
) -> Optional[EvChargingGrowthResult]:
    """
    Correlate monthly EV growth rates with a metals ETF price.
    Returns the analysis result if successful, or None if data already fetched today.
    """

    storage_path = Path(settings.STORAGE_FILE_PATH)

    if already_fetched_today(storage_path, metals_etf):
        console.print(
            Panel(f"[yellow]Skipping analysis for {metals_etf} (already fetched today).",
                  title="Analysis Status")
        )
        return None
    
    console.print(
        Panel(
            f"[blue]Analyzing EV charging growth correlation with {metals_etf} over {months} months",
            title="Analysis Status"
        )
    )

    prompt = f"""
    Correlate EV charger growth vs. {metals_etf} closing prices over {months} months.
    1) Use fetch_ev_charger_growth(months={months})
    2) Use fetch_metals_prices(symbol={metals_etf}, months={months})
    3) Compute correlation
    4) Return a JSON with keys (metals_etf_symbol, correlation, recommendation)
    """
    result = await agent.run(prompt)
    final = result.data

    console.print(
        Panel(
            f"[green]Correlation: {final.correlation:.3f}\n"
            f"Recommendation: {final.recommendation}",
            title=f"Analysis Results for {metals_etf}"
        )
    )

    # Append to CSV
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    with storage_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            final.metals_etf_symbol,
            final.correlation,
            final.recommendation
        ])

    return final