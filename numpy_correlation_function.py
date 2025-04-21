import numpy as np # type: ignore

# Aligned lists
ev_charger_growth = [0.0, 0.0, 0.0, 13.0, 7.0]
pplt_prices = [243.44, 243.93, 244.67, 242.86, 242.95]

# Calculate Pearson correlation coefficient
correlation = np.corrcoef(ev_charger_growth, pplt_prices)[0, 1]
correlation
