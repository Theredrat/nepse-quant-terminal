import sqlite3

conn = sqlite3.connect('nepse_market_data.db')

# ANALYSIS 1: How deep is the post-listing dip before the run?
# Find: listing price, lowest price in first 30 days, then ATH
print("="*80)
print("ANALYSIS 1 — Post Listing Dip Depth (first 30 days)")
print("="*80)

stocks = conn.execute("""
    SELECT sp.symbol, MIN(sp.date) as list_date
    FROM stock_prices sp
    INNER JOIN companies c ON sp.symbol = c.symbol
    WHERE c.sector IN (
        'Commercial Banks','Development Banks','Finance',
        'Hotels And Tourism','Hydro Power','Investment',
        'Life Insurance','Manufacturing And Processing',
        'Microfinance','Non Life Insurance','Others','Tradings'
    )
    GROUP BY sp.symbol
    HAVING MIN(sp.date) >= '2022-01-01'
    AND COUNT(DISTINCT sp.date) >= 60
    ORDER BY MIN(sp.date) DESC
""").fetchall()

print(f"{'Symbol':<10} {'List Rs':<10} {'30d Low':<10} {'Dip%':<10} {'ATH Rs':<10} {'Run%':<10} {'ATH days':<10}")
print('-'*70)

for sym, list_date in stocks:
    prices = conn.execute("""
        SELECT date, close FROM stock_prices 
        WHERE symbol=? ORDER BY date ASC
    """, (sym,)).fetchall()
    
    if len(prices) < 10:
        continue
    
    list_price = prices[0][1]
    
    # First 30 trading days
    first30 = prices[:30]
    low30 = min(p[1] for p in first30)
    dip_pct = (low30 - list_price) / list_price * 100
    
    # ATH and when
    ath = max(p[1] for p in prices)
    ath_idx = [p[1] for p in prices].index(ath)
    ath_days = ath_idx
    run_pct = (ath - low30) / low30 * 100
    
    print(f"{sym:<10} {list_price:<10.0f} {low30:<10.0f} {dip_pct:<+10.1f} {ath:<10.0f} {run_pct:<+10.1f} {ath_days:<10}")

conn.close()
