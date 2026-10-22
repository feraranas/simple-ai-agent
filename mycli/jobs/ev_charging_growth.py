import csv
from datetime import datetime, date, timezone
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich.console import Console
from rich.panel import Panel

from mycli.jobs.fetch_ev_charger_growth import fetch_ev_charger_growth as fetch_ev_charger_growth_counts
from mycli.jobs.fetch_metal_prices import fetch_metals_prices_ind
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
    return await fetch_ev_charger_growth_counts(months, max_results=5000)


@agent.tool
async def fetch_metals_prices(
    ctx: RunContext[None],
    symbol: str,
    months: int
) -> List[float]:
    """Fetch monthly EOD prices for a metals ETF from Marketstack (real API calls)."""
    return await fetch_metals_prices_ind(symbol, months)


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