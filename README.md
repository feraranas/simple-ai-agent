## Run:
- python -m .venv venv
- pip install -r requirements.txt

#### run each module

1. Execute agents & analysis: ```python main.py ev-charging-growth --months --symbol PPLT```
2. Fetch EV Charging Status: ```python main.py fetch-ev-charger-growth --months 5```
3. Fetch ETF Metal prices: ```python main.py fetch-etf-metal-prices --months 5 --symbol GLD``` 


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

#### Obtain API Keys from:

- OPENCHARGEMAP_API_KEY in https://openchargemap.org/site/profile/applications
- MARKETSTACK_API_KEY = https://marketstack.com/dashboard 
- OPENAI_API_KEY = https://platform.openai.com/settings/


