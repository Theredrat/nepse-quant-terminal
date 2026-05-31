# Live test: what does _calc_relative_strength actually return?
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

if df.empty:
    print('EMPTY - no data')
else:
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
    
    print(f'Results count: {len(results)}')
    rdf = pd.DataFrame(results).dropna(subset=['ret5'])
    print(f'After dropna: {len(rdf)}')
    print(f'Sample:\n{rdf.head(3).to_string()}')
