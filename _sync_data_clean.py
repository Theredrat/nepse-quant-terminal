import os, json, sqlite3, subprocess, datetime

DB = 'nepse_market_data.db'
DATA_DIR = 'daily_data'
LOG_FILE = '_import_log.json'

def git_pull():
    try:
        r=subprocess.run(['git','pull'],capture_output=True,text=True,timeout=30)
        print('Git pull:',r.stdout.strip() or 'OK')
        return True
    except Exception as e:
        print('Git failed:',e)
        return False

def git_delete_and_push(fnames):
    try:
        for fname in fnames:
            path=os.path.join(DATA_DIR,fname)
            subprocess.run(['git','rm','--cached',path],capture_output=True)
            if os.path.exists(path): os.remove(path)
        subprocess.run(['git','add','-A'],capture_output=True)
        msg='Cleanup: '+str(len(fnames))+' files over 1 yr'
        r=subprocess.run(['git','commit','-m',msg],capture_output=True,text=True)
        if 'nothing' not in r.stdout:
            subprocess.run(['git','push'],capture_output=True)
            print('Deleted from GitHub:',len(fnames),'files')
    except Exception as e:
        print('Git delete failed:',e)

def load_log():
    if os.path.exists(LOG_FILE):
        try: return json.load(open(LOG_FILE,encoding='utf-8'))
        except: pass
    return {}

def save_log(log):
    json.dump(log,open(LOG_FILE,'w',encoding='utf-8'),indent=2)

def get_imported_dates(conn):
    try:
        rows=conn.execute('SELECT DISTINCT date FROM broker_activity').fetchall()
        return set(r[0] for r in rows)
    except: return set()

def import_json(conn,path,date_str):
    data=json.load(open(path,encoding='utf-8'))
    brokers=data.get('brokers',{})
    rows=[]
    for sym,bdata in brokers.items():
        for broker_id,net_val in bdata.items():
            rows.append((sym,date_str,str(broker_id),float(net_val)))
    if rows:
        sql='INSERT OR IGNORE INTO broker_activity (symbol,date,broker_id,net_val) VALUES (?,?,?,?)'
        conn.executemany(sql,rows)
        conn.commit()
        print('  Imported',date_str,'-',len(rows),'rows')
        return True
    return False

def ensure_table(conn):
    sql='CREATE TABLE IF NOT EXISTS broker_activity (symbol TEXT, date TEXT, broker_id TEXT, net_val REAL, UNIQUE (symbol,date,broker_id))'
    conn.execute(sql)
    conn.commit()

def cleanup_old_files(log):
    today=datetime.date.today()
    to_delete=[]
    for fname,import_date_str in list(log.items()):
        try:
            import_date=datetime.date.fromisoformat(import_date_str)
            if (today-import_date).days>=365:
                if os.path.exists(os.path.join(DATA_DIR,fname)):
                    to_delete.append(fname)
        except: pass
    if to_delete:
        git_delete_and_push(to_delete)
        for fname in to_delete: del log[fname]
        save_log(log)
        print('Cleaned up',len(to_delete),'files (1 yr old)')
    return log

def get_imported_price_dates(conn):
    try:
        rows = conn.execute("SELECT DISTINCT date FROM stock_prices").fetchall()
        return set(r[0] for r in rows)
    except:
        return set()

def import_price_json(conn, path, date_str):
    import json
    data = json.load(open(path, encoding="utf-8"))
    prices = data.get("prices", [])
    rows = []
    for p in prices:
        sym = p.get("symbol", "")
        if not sym:
            continue
        rows.append((
            sym, date_str,
            p.get("open", 0),
            p.get("high", 0),
            p.get("low", 0),
            p.get("close", 0),
            p.get("volume", 0),
        ))
    if rows:
        conn.executemany(
            "INSERT OR REPLACE INTO stock_prices (symbol,date,open,high,low,close,volume) VALUES (?,?,?,?,?,?,?)",
            rows
        )
        conn.commit()
        print("  Prices imported", date_str, "-", len(rows), "rows")
        return True
    return False

def ensure_prices_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS stock_prices (
        symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, volume REAL,
        UNIQUE(symbol, date)
    )""")
    conn.commit()

def main():
    print('Pulling latest data from GitHub...')
    git_pull()
    if not os.path.isdir(DATA_DIR):
        print('No daily_data folder yet')
        return
    conn=sqlite3.connect(DB)
    ensure_table(conn)
    imported=get_imported_dates(conn)
    log=load_log()
    files=sorted(f for f in os.listdir(DATA_DIR) if f.startswith('broker_') and f.endswith('.json'))
    new_count=0
    today_str=datetime.date.today().isoformat()
    for fname in files:
        date_str=fname[7:17]
        if date_str in imported:
            if fname not in log: log[fname]=today_str
            continue
        path=os.path.join(DATA_DIR,fname)
        if import_json(conn,path,date_str):
            log[fname]=today_str
            new_count+=1
    conn.close()
    save_log(log)
    # Import price files
    price_imported = get_imported_price_dates(conn2 := sqlite3.connect(DB))
    ensure_prices_table(conn2)
    price_files = sorted(f for f in os.listdir(DATA_DIR) if f.startswith('prices_') and f.endswith('.json'))
    price_new = 0
    for fname in price_files:
        date_str = fname[7:17]
        if date_str not in price_imported:
            path = os.path.join(DATA_DIR, fname)
            if import_price_json(conn2, path, date_str):
                price_new += 1
    conn2.close()
    if price_new:
        print("Price days imported:", price_new)

    if new_count: print('Imported',new_count,'new days')
    else: print('DB up to date - no new data')
    cleanup_old_files(log)

if __name__=='__main__':
    main()
