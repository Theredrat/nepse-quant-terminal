import sqlite3

conn = sqlite3.connect('nepse_market_data.db')

print("="*80)
print("SECTOR ANALYSIS — ATH by Sector for IPO Stocks")
print("="*80)

rows = conn.execute("""
    SELECT 
        c.sector,
        sp.symbol,
        MIN(sp.date) as list_date,
        (SELECT close FROM stock_prices WHERE symbol=sp.symbol ORDER BY date ASC LIMIT 1) as list_price,
        (SELECT MAX(close) FROM stock_prices WHERE symbol=sp.symbol) as ath,
        (SELECT close FROM stock_prices WHERE symbol=sp.symbol ORDER BY date DESC LIMIT 1) as cur_price,
        f.public_shares,
        f.promoter_pct,
        f.public_pct
    FROM stock_prices sp
    INNER JOIN companies c ON sp.symbol = c.symbol
    LEFT JOIN fundamentals f ON sp.symbol = f.symbol
    WHERE c.sector IN (
        'Commercial Banks','Development Banks','Finance',
        'Hotels And Tourism','Hydro Power','Investment',
        'Life Insurance','Manufacturing And Processing',
        'Microfinance','Non Life Insurance','Others','Tradings'
    )
    GROUP BY sp.symbol
    HAVING MIN(sp.date) >= '2022-01-01'
    AND COUNT(DISTINCT sp.date) >= 30
    ORDER BY c.sector, ath DESC
""").fetchall()

current_sector = None
sector_aths = {}

for r in rows:
    sector, sym, list_date, list_price, ath, cur, pub_shares, prom_pct, pub_pct = r
    if not list_price or not ath:
        continue
    
    if sector not in sector_aths:
        sector_aths[sector] = []
    sector_aths[sector].append((sym, list_price, ath, pub_shares, prom_pct, pub_pct))

for sector, stocks in sorted(sector_aths.items()):
    aths = [s[2] for s in stocks if s[2]]
    avg_ath = sum(aths)/len(aths) if aths else 0
    max_ath = max(aths) if aths else 0
    min_ath = min(aths) if aths else 0
    
    print(f"\n{sector} ({len(stocks)} IPOs) — ATH: avg Rs {avg_ath:.0f} | min Rs {min_ath:.0f} | max Rs {max_ath:.0f}")
    print(f"  {'Symbol':<10} {'List Rs':<10} {'ATH Rs':<10} {'Public Shares':<16} {'Prom%':<8} {'Pub%':<6}")
    for sym, lp, ath, pub, prom, pub_pct in stocks[:8]:
        pub_str = f"{pub:,.0f}" if pub else "N/A"
        prom_str = f"{prom:.0f}%" if prom else "N/A"
        pub_pct_str = f"{pub_pct:.0f}%" if pub_pct else "N/A"
        print(f"  {sym:<10} {lp:<10.0f} {ath:<10.0f} {pub_str:<16} {prom_str:<8} {pub_pct_str:<6}")

conn.close()
