import sqlite3, sys
sys.path.insert(0, '.')
import importlib.util, types

# Directly run just _load_sector_prices and _sector_returns
exec(open('nepse_scanner.py', encoding='utf-8').read().split('def analyze_sector_trend')[0])

prices = _load_sector_prices()
print('prices columns:', prices.columns.tolist() if not prices.empty else 'EMPTY')
print('sector values sample:', prices['sector'].value_counts().head(10) if not prices.empty else 'N/A')

result = _sector_returns(prices)
print('\\n_sector_returns keys (first 5):')
for k, v in list(result.items())[:5]:
    print(f'  key={repr(k)}  value={v}')
