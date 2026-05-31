import sqlite3, pandas as pd

conn = sqlite3.connect('nepse_market_data.db')
df = pd.read_sql("""
    SELECT sp.symbol, c.sector, sp.date, sp.close
    FROM stock_prices sp
    JOIN companies c ON sp.symbol = c.symbol
    WHERE sp.date >= date('now', '-35 days')
    ORDER BY sp.symbol, sp.date
""", conn)
conn.close()

print('Total rows:', len(df))
print('Sectors found:', df['sector'].nunique())
print('Sample symbols per sector:')
print(df.groupby('sector')['symbol'].nunique())

# Simulate what _sector_returns does
df['date'] = pd.to_datetime(df['date'])
sector_results = {}
for symbol, grp in df.groupby('symbol'):
    grp = grp.sort_values('date').drop_duplicates('date')
    if len(grp) < 6:
        continue
    sector = grp['sector'].iloc[0]
    closes = grp['close'].values
    def pct(n):
        if len(closes) <= n: return None
        return (closes[-1] / closes[-n-1] - 1) * 100
    if sector not in sector_results:
        sector_results[sector] = []
    sector_results[sector].append({'ret5': pct(5), 'ret10': pct(10), 'ret20': pct(20)})

print('\nSector results keys:', list(sector_results.keys())[:5])
print('First sector sample:', list(sector_results.items())[0])
