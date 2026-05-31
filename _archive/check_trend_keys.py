import sys, types
src = open('nepse_scanner.py', encoding='utf-8').read()
mod = types.ModuleType('t')
exec(compile(src[:src.find('\nif __name__')], 'nepse_scanner.py', 'exec'), mod.__dict__)

import sqlite3, pandas as pd
conn = sqlite3.connect('nepse_market_data.db')
df = pd.read_sql("""
    SELECT sp.symbol, c.sector, sp.date, sp.close
    FROM stock_prices sp JOIN companies c ON sp.symbol = c.symbol
    WHERE sp.date >= date('now', '-35 days')
    ORDER BY sp.symbol, sp.date
""", conn)
conn.close()

result = mod._sector_returns(df)
print('Type:', type(result))
print('Keys:', list(result.keys()))
for k, v in result.items():
    print(f'  {repr(k)}: {v}')
