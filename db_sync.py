import sqlite3, os

src_path = r"data\nepse_market_data.db"
dst_path = "nepse_market_data.db"

if not os.path.exists(src_path):
    print("Source DB not found, skipping sync.")
    exit()

src = sqlite3.connect(src_path)
dst = sqlite3.connect(dst_path)

src_dates = {r[0] for r in src.execute("SELECT DISTINCT date FROM stock_prices")}
dst_dates = {r[0] for r in dst.execute("SELECT DISTINCT date FROM stock_prices")}
new_dates = src_dates - dst_dates

from datetime import date
today = date.today().isoformat()
if today in src_dates:
    rows = src.execute("SELECT * FROM stock_prices WHERE date=?", (today,)).fetchall()
    dst.execute("DELETE FROM stock_prices WHERE date=?", (today,))
    dst.executemany("INSERT OR IGNORE INTO stock_prices VALUES (?,?,?,?,?,?,?)", rows)
    dst.commit()
    print(f"Force-synced today {today}: {len(rows)} rows")
if not new_dates - {today}:
    print("Root DB already up to date.")
else:
    for d in sorted(new_dates - {today}):
        rows = src.execute("SELECT * FROM stock_prices WHERE date=?", (d,)).fetchall()
        dst.executemany("INSERT OR IGNORE INTO stock_prices VALUES (?,?,?,?,?,?,?)", rows)
        print(f"Synced {len(rows)} rows for {d}")
    dst.commit()
    print("Sync complete.")
