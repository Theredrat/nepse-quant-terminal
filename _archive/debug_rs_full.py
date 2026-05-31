import sqlite3
conn = sqlite3.connect('nepse_market_data.db')
cur = conn.cursor()

# What is the most recent date in stock_prices?
cur.execute("SELECT MAX(date), MIN(date), COUNT(DISTINCT date) FROM stock_prices WHERE date >= date('now', '-35 days')")
print('Last 35 days:', cur.fetchone())

cur.execute("SELECT MAX(date) FROM stock_prices")
print('Most recent date ever:', cur.fetchone())

# Test exact query from _calc_relative_strength
import pandas as pd
df = pd.read_sql("""
    SELECT sp.symbol, c.sector, sp.date, sp.close
    FROM stock_prices sp
    JOIN companies c ON sp.symbol = c.symbol
    WHERE sp.date >= date('now', '-35 days')
    ORDER BY sp.symbol, sp.date
""", conn)
print('_calc_relative_strength query rows:', len(df))

# Also check what analyze_relative_strength gets back
# Simulate _calc_relative_strength full logic
df['date'] = pd.to_datetime(df['date'])
results = []
for symbol, grp in df.groupby('symbol'):
    grp = grp.sort_values('date').drop_duplicates('date')
    if len(grp) < 6:
        continue
    sector = grp['sector'].iloc[0]
    closes = grp['close'].values
    def pct(n):
        if len(closes) <= n: return None
        return (closes[-1] / closes[-n-1] - 1) * 100
    results.append({'symbol': symbol, 'sector': sector,
                    'ret5': pct(5), 'ret10': pct(10), 'ret20': pct(20)})

import pandas as pd2
rdf = pd.DataFrame(results).dropna(subset=['ret5'])
savg = rdf.groupby('sector')[['ret5','ret10','ret20']].mean().rename(
    columns={'ret5':'sec5','ret10':'sec10','ret20':'sec20'})
rdf = rdf.join(savg, on='sector')
rdf['rs5']  = rdf['ret5']  - rdf['sec5']
rdf['rs10'] = rdf['ret10'] - rdf['sec10']
rdf['rs20'] = rdf['ret20'] - rdf['sec20']
rdf['rs_score'] = rdf['rs5']*0.50 + rdf['rs10'].fillna(0)*0.30 + rdf['rs20'].fillna(0)*0.20
final = rdf.sort_values('rs_score', ascending=False).to_dict('records')
print(f'Final output length: {len(final)}')
print(f'First record keys: {list(final[0].keys()) if final else "EMPTY"}')
print(f'First record: {final[0] if final else "EMPTY"}')
conn.close()
