import re, sqlite3, csv, sys, os
from datetime import date

def parse_num(s):
    s = str(s).strip().replace(",","")
    if not s or s in ("-","N/A","None","0"): return 0.0
    try:
        s2 = s.replace(" ","")
        if s2.endswith("Cr"): return float(s2[:-2])*1e7
        if s2.endswith("L"):  return float(s2[:-1])*1e5
        if s2.endswith("K"):  return float(s2[:-1])*1e3
        return float(re.sub(r"[^\d.\-]","",s))
    except: return 0.0

def get_col(row, *keys):
    for k in keys:
        if k in row and str(row[k]).strip() not in ("","None"):
            return str(row[k]).strip()
    return "0"

def setup_db(conn):
    conn.execute("DROP TABLE IF EXISTS broker_holdings")
    conn.execute("""CREATE TABLE broker_holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT, broker_id TEXT, broker_name TEXT,
        hold_vol REAL DEFAULT 0, hold_amt REAL DEFAULT 0,
        buy_vol REAL DEFAULT 0, buy_amt REAL DEFAULT 0, avg_buy REAL DEFAULT 0,
        sell_vol REAL DEFAULT 0, sell_amt REAL DEFAULT 0, avg_sell REAL DEFAULT 0,
        hb_ratio REAL DEFAULT 0, imported_date TEXT,
        UNIQUE(symbol, broker_id))""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bh_sym ON broker_holdings(symbol)")
    conn.commit()

def import_csv(symbol, filepath, conn):
    rows = []
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rank = get_col(row, "Rank")
                name = get_col(row, "Broker Name","Broker")
                bid  = rank if rank and rank!="0" else name[:20]
                hv   = parse_num(get_col(row,"Hold Vol","Holding Vol"))
                bv   = parse_num(get_col(row,"Buy Vol"))
                sv   = parse_num(get_col(row,"Sell Vol"))
                ab   = parse_num(get_col(row,"Avg Buy"))
                as_  = parse_num(get_col(row,"Avg Sell"))
                hb   = parse_num(get_col(row,"H/B Ratio","HB Ratio"))
                rows.append((symbol.upper(),bid,name,hv,0.0,bv,0.0,ab,sv,0.0,as_,hb,str(date.today())))
            except: pass

    if not rows:
        print(f"ERROR: No rows for {symbol}")
        return

    ins = 0
    for r in rows:
        try:
            conn.execute("INSERT OR REPLACE INTO broker_holdings (symbol,broker_id,broker_name,hold_vol,hold_amt,buy_vol,buy_amt,avg_buy,sell_vol,sell_amt,avg_sell,hb_ratio,imported_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", r)
            ins += 1
        except: pass
    conn.commit()

    c = conn.cursor()
    c.execute("SELECT broker_name,hold_vol,buy_vol,sell_vol,hb_ratio FROM broker_holdings WHERE symbol=? ORDER BY hold_vol DESC LIMIT 10",(symbol.upper(),))
    top = c.fetchall()
    c.execute("SELECT COUNT(*),SUM(hold_vol) FROM broker_holdings WHERE symbol=?",(symbol.upper(),))
    cnt,total = c.fetchone()

    print(f"\nOK - {symbol}: {ins} brokers | Total held: {int(total or 0):,}")
    print(f"{'Broker':<30} {'Hold':>10} {'Bought':>10} {'Sold':>10} {'H/B%':>7} Signal")
    print("-"*75)
    for r in top:
        sig = "STRONG HOLD" if r[4]>=60 else "HOLDING" if r[4]>=30 else "TRADING" if r[4]>=15 else "DISTRIB" if r[4]>0 else "NET SELL"
        print(f"{r[0]:<30} {int(r[1]):>10,} {int(r[2]):>10,} {int(r[3]):>10,} {r[4]:>7.1f} {sig}")

conn = sqlite3.connect("nepse_market_data.db")
setup_db(conn)

for sym in ["NICL","SJCL"]:
    fp = f"sharehub_data/{sym}_brokers.csv"
    if os.path.exists(fp):
        import_csv(sym, fp, conn)
    else:
        print(f"File missing: {fp}")

conn.close()
