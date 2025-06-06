# Simple AI Agent with 2 tools and an output validator

There's a cron job that runs daily 6am CST, it runs the agent which outputs the following correlation analysis between 2 markets: 1) ev charging stations, 2) etf of metals (gold, platinum, etc):

<p align="center" width=250px>
  <img src="https://github.com/feraranas/simple-ai-agent/blob/main/output.png" />
</p>

## Obtain API Keys from:

- OPENCHARGEMAP_API_KEY in https://openchargemap.org/site/profile/applications
- MARKETSTACK_API_KEY = https://marketstack.com/dashboard 
- OPENAI_API_KEY = https://platform.openai.com/settings/

## Setup:
- python -m .venv venv
- source .venv/bin/activate
- pip install -r requirements.txt

## Run:

1. Execute agents & analysis: ```python main.py ev-charging-growth --months 5 --metals-etf PPLT```

#### informative on the 2 tools the agent uses
- Fetch EV Charging Status: ```python main.py fetch-ev-charger-growth --months 5```
- Fetch ETF Metal prices: ```python main.py fetch-etf-metal-prices --months 5 --symbol GLD``` 


## Code Overview
#### This project is laid out as a Typer Python CLI app. This is the repo structure:

```bash
ev-charging-growth-cli/
├── .github/
│   └── workflows/
│       └── cron.yml
│
├── mycli/
│   ├── __init__.py
│   └── jobs/
│       └── ev_charging_growth.py
│
├── tests/
│   └── integration/
│       └── test_ev_charging_tools.py
│
├── data.csv
├── settings.py
├── main.py
├── requirements.txt
├── README.md
└── .env  (not in repo - contains secrets)
```
