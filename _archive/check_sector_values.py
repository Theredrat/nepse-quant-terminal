import sqlite3
conn = sqlite3.connect('nepse_market_data.db')
import pandas as pd

# What sector values exist in companies table?
print('=== companies.sector values ===')
df = pd.read_sql("SELECT sector, COUNT(*) as cnt FROM companies GROUP BY sector ORDER BY cnt DESC", conn)
print(df.to_string())

# What does _load_sector_prices actually return now?
print('\n=== _load_sector_prices sample (first 10 rows) ===')
df2 = pd.read_sql("""
    SELECT sp.symbol, c.sector, sp.date, sp.close
    FROM stock_prices sp
    JOIN companies c ON sp.symbol = c.symbol
    WHERE sp.date >= date('now', '-35 days')
    ORDER BY sp.symbol, sp.date
    LIMIT 10
""", conn)
print(df2.to_string())
print('\nsector unique values:', df2['sector'].unique().tolist())

conn.close()
