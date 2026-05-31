import sqlite3
conn = sqlite3.connect('nepse_market_data.db')
c = conn.cursor()

print("=== DATA GAPS ANALYSIS ===\n")

# Stock prices
c.execute("SELECT COUNT(*), MIN(date), MAX(date), COUNT(DISTINCT symbol) FROM stock_prices")
cnt, mn, mx, syms = c.fetchone()
print(f"stock_prices: {cnt} rows | {syms} symbols | {mn} to {mx}")

# Fundamentals
c.execute("SELECT COUNT(*), MIN(date), MAX(date), COUNT(DISTINCT symbol) FROM fundamentals")
cnt, mn, mx, syms = c.fetchone()
print(f"fundamentals: {cnt} rows | {syms} symbols | {mn} to {mx}")

# Broker activity
c.execute("SELECT COUNT(*), MIN(date), MAX(date), COUNT(DISTINCT symbol) FROM broker_activity")
cnt, mn, mx, syms = c.fetchone()
print(f"broker_activity: {cnt} rows | {syms} symbols | {mn} to {mx}")

# Quarterly earnings
c.execute("SELECT COUNT(*), MIN(report_date), MAX(report_date), COUNT(DISTINCT symbol) FROM quarterly_earnings")
cnt, mn, mx, syms = c.fetchone()
print(f"quarterly_earnings: {cnt} rows | {syms} symbols | {mn} to {mx}")

# Check if shareholding table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
has_holding = any('hold' in t.lower() or 'share' in t.lower() or 'owner' in t.lower() for t in tables)
print(f"\nShareholding table: {'EXISTS' if has_holding else 'MISSING'}")

# Check fundamentals columns for shareholding data
c.execute("PRAGMA table_info(fundamentals)")
cols = [r[1] for r in c.fetchall()]
print(f"Fundamentals columns: {cols}")

# Check what fundamentals data looks like
c.execute("SELECT * FROM fundamentals LIMIT 3")
rows = c.fetchall()
print(f"\nFundamentals sample:")
for r in rows:
    print(f"  {r}")

# Check broker activity sample
c.execute("SELECT * FROM broker_activity LIMIT 3")
rows = c.fetchall()
print(f"\nBroker activity sample:")
for r in rows:
    print(f"  {r}")

conn.close()
