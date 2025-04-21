import asyncio
import typer

from mycli.jobs.ev_charging_growth import run_ev_charging_growth
from mycli.jobs.fetch_ev_charger_growth import fetch_ev_charger_growth_ind
from mycli.jobs.fetch_metal_prices import fetch_metals_prices_ind

app = typer.Typer(help="GenAI CLI for investment investigations.")


@app.command("ev-charging-growth")
def ev_charging_growth_cli(
    months: int = 5,
    metals_etf: str = "PPLT"
):
    '''Full agent call'''
    asyncio.run(run_ev_charging_growth(months, metals_etf))


@app.command("fetch-ev-charger-growth")
def fetch_ev_charger_growth_typer(
    months: int = 5
):
    '''Partial API call to EV Open Charge Map'''
    asyncio.run(fetch_ev_charger_growth_ind(months))


@app.command("fetch-etf-metal-prices")
def fetch_etf_metal_prices(
    symbol: str = "GLD",
    months: int = 5
):
    '''Partial API call to ETF metal prices'''
    asyncio.run(fetch_metals_prices_ind(symbol, months))

if __name__ == "__main__":
    app()
