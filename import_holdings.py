import sqlite3, re, os, json
from datetime import date

db_path = "nepse_market_data.db"
data_dir = "sharehub_data"
os.makedirs(data_dir, exist_ok=True)

def parse_nepali_number(s):
    s = str(s).strip().replace(",", "")
    try:
        if "Arab" in s:
            return float(re.sub(r"[^\d.]", "", s.replace("Arab",""))) * 1e9
        elif "Cr" in s:
            return float(re.sub(r"[^\d.]", "", s.replace("Cr",""))) * 1e7
        elif "L" in s and "Lakh" not in s:
            return float(re.sub(r"[^\d.]", "", s.replace("L",""))) * 1e5
        elif "K" in s:
            return float(re.sub(r"[^\d.]", "", s.replace("K",""))) * 1e3
        else:
            return float(re.sub(r"[^\d.-]", "", s)) if s else 0
    except:
        return 0

def setup_holdings_table():
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            broker_id TEXT NOT NULL,
            broker_name TEXT NOT NULL,
            hold_vol REAL DEFAULT 0,
            hold_amt REAL DEFAULT 0,
            buy_vol REAL DEFAULT 0,
            buy_amt REAL DEFAULT 0,
            avg_buy REAL DEFAULT 0,
            sell_vol REAL DEFAULT 0,
            sell_amt REAL DEFAULT 0,
            avg_sell REAL DEFAULT 0,
            period_days INTEGER DEFAULT 224,
            imported_date TEXT,
            UNIQUE(symbol, broker_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bh_symbol ON broker_holdings(symbol)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bh_broker ON broker_holdings(broker_id)")
    conn.commit()
    conn.close()
    print("Table broker_holdings ready")

def parse_and_import(symbol, raw_text):
    lines = [l.strip() for l in raw_text.strip().splitlines()]
    rows = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\d+$", line):
            broker_id = line.strip()
            # Skip empty lines
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j >= len(lines):
                i = j
                continue
            broker_name = lines[j].strip()
            j += 1
            # Skip empty lines
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j >= len(lines):
                i = j
                continue
            data_line = lines[j].strip()
            j += 1

            # Extract all numbers and amount strings from data line
            # Pattern: number, Rs. amount, number, Rs. amount, Rs. price, number, pct, ...
            tokens = re.findall(
                r"Rs\.\s*[\d,]+(?:\.\d+)?\s*(?:Arab|Cr|L|K)?|-?[\d,]+(?:\.\d+)?",
                data_line
            )
            cleaned = []
            for t in tokens:
                t = t.strip()
                if t.startswith("Rs."):
                    cleaned.append(parse_nepali_number(t.replace("Rs.", "").strip()))
                else:
                    try:
                        cleaned.append(float(t.replace(",", "")))
                    except:
                        cleaned.append(0)

            if len(cleaned) >= 6:
                hold_vol  = cleaned[0] if len(cleaned) > 0 else 0
                hold_amt  = cleaned[1] if len(cleaned) > 1 else 0
                buy_vol   = cleaned[2] if len(cleaned) > 2 else 0
                buy_amt   = cleaned[3] if len(cleaned) > 3 else 0
                avg_buy   = cleaned[4] if len(cleaned) > 4 else 0
                sell_vol  = cleaned[6] if len(cleaned) > 6 else 0
                sell_amt  = cleaned[7] if len(cleaned) > 7 else 0
                avg_sell  = cleaned[8] if len(cleaned) > 8 else 0
                rows.append((
                    symbol.upper(), broker_id, broker_name,
                    hold_vol, hold_amt, buy_vol, buy_amt, avg_buy,
                    sell_vol, sell_amt, avg_sell,
                    224, str(date.today())
                ))
            i = j
        else:
            i += 1

    if not rows:
        print(f"WARNING: No rows parsed for {symbol}")
        return 0

    # Save raw to file first
    raw_file = f"{data_dir}/{symbol.upper()}_raw.txt"
    with open(raw_file, "w", encoding="utf-8") as f:
        f.write(raw_text)

    # Import to DB
    conn = sqlite3.connect(db_path)
    inserted = 0
    for row in rows:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO broker_holdings
                (symbol, broker_id, broker_name, hold_vol, hold_amt,
                 buy_vol, buy_amt, avg_buy, sell_vol, sell_amt, avg_sell,
                 period_days, imported_date)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, row)
            inserted += 1
        except Exception as e:
            print(f"Error inserting {row[1]}: {e}")
    conn.commit()

    # Show top 5 holders
    c = conn.cursor()
    c.execute("""
        SELECT broker_id, broker_name, hold_vol, buy_vol, sell_vol
        FROM broker_holdings WHERE symbol=?
        ORDER BY hold_vol DESC LIMIT 5
    """, (symbol.upper(),))
    top = c.fetchall()
    conn.close()

    print(f"OK - {symbol}: {inserted} brokers imported")
    print(f"Top 5 holders:")
    for r in top:
        print(f"  Broker {r[0]} ({r[1][:20]}) Hold: {int(r[2]):,} | Bought: {int(r[3]):,} | Sold: {int(r[4]):,}")
    return inserted

def show_summary():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT symbol, COUNT(*), SUM(hold_vol) FROM broker_holdings GROUP BY symbol ORDER BY symbol")
    rows = c.fetchall()
    conn.close()
    print(f"\n=== HOLDINGS SUMMARY ===")
    for r in rows:
        print(f"  {r[0]}: {r[1]} brokers | Total held: {int(r[2]):,} shares")

setup_holdings_table()
print("Ready! Now run: python import_stock.py SYMBOL")
print("Paste data will be read from sharehub_data/SYMBOL_raw.txt")
