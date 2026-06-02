import os, json, sqlite3, subprocess, datetime

DB = chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(95)+chr(100)+chr(97)+chr(116)+chr(97)+chr(46)+chr(100)+chr(98)
DATA_DIR = chr(100)+chr(97)+chr(105)+chr(108)+chr(121)+chr(95)+chr(100)+chr(97)+chr(116)+chr(97)
LOG_FILE = chr(95)+chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(95)+chr(108)+chr(111)+chr(103)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110)

def git_pull():
    try:
        r=subprocess.run([chr(103)+chr(105)+chr(116),chr(112)+chr(117)+chr(108)+chr(108)],capture_output=True,text=True,timeout=30)
        print(chr(71)+chr(105)+chr(116)+chr(32)+chr(112)+chr(117)+chr(108)+chr(108)+chr(58),r.stdout.strip() or chr(79)+chr(75))
        return True
    except Exception as e:
        print(chr(71)+chr(105)+chr(116)+chr(32)+chr(102)+chr(97)+chr(105)+chr(108)+chr(101)+chr(100)+chr(58),e)
        return False

def git_delete_and_push(fnames):
    try:
        for fname in fnames:
            path=os.path.join(DATA_DIR,fname)
            subprocess.run([chr(103)+chr(105)+chr(116),chr(114)+chr(109),chr(45)+chr(45)+chr(99)+chr(97)+chr(99)+chr(104)+chr(101)+chr(100),path],capture_output=True)
            if os.path.exists(path): os.remove(path)
        subprocess.run([chr(103)+chr(105)+chr(116),chr(97)+chr(100)+chr(100),chr(45)+chr(65)],capture_output=True)
        msg=chr(67)+chr(108)+chr(101)+chr(97)+chr(110)+chr(117)+chr(112)+chr(58)+chr(32)+str(len(fnames))+chr(32)+chr(102)+chr(105)+chr(108)+chr(101)+chr(115)+chr(32)+chr(111)+chr(118)+chr(101)+chr(114)+chr(32)+chr(49)+chr(32)+chr(121)+chr(114)
        r=subprocess.run([chr(103)+chr(105)+chr(116),chr(99)+chr(111)+chr(109)+chr(109)+chr(105)+chr(116),chr(45)+chr(109),msg],capture_output=True,text=True)
        if chr(110)+chr(111)+chr(116)+chr(104)+chr(105)+chr(110)+chr(103) not in r.stdout:
            subprocess.run([chr(103)+chr(105)+chr(116),chr(112)+chr(117)+chr(115)+chr(104)],capture_output=True)
            print(chr(68)+chr(101)+chr(108)+chr(101)+chr(116)+chr(101)+chr(100)+chr(32)+chr(102)+chr(114)+chr(111)+chr(109)+chr(32)+chr(71)+chr(105)+chr(116)+chr(72)+chr(117)+chr(98)+chr(58),len(fnames),chr(102)+chr(105)+chr(108)+chr(101)+chr(115))
    except Exception as e:
        print(chr(71)+chr(105)+chr(116)+chr(32)+chr(100)+chr(101)+chr(108)+chr(101)+chr(116)+chr(101)+chr(32)+chr(102)+chr(97)+chr(105)+chr(108)+chr(101)+chr(100)+chr(58),e)

def load_log():
    if os.path.exists(LOG_FILE):
        try: return json.load(open(LOG_FILE,encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)))
        except: pass
    return {}

def save_log(log):
    json.dump(log,open(LOG_FILE,chr(119),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)),indent=2)

def get_imported_dates(conn):
    try:
        rows=conn.execute(chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(68)+chr(73)+chr(83)+chr(84)+chr(73)+chr(78)+chr(67)+chr(84)+chr(32)+chr(100)+chr(97)+chr(116)+chr(101)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(97)+chr(99)+chr(116)+chr(105)+chr(118)+chr(105)+chr(116)+chr(121)).fetchall()
        return set(r[0] for r in rows)
    except: return set()

def import_json(conn,path,date_str):
    data=json.load(open(path,encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)))
    brokers=data.get(chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(115),{})
    rows=[]
    for sym,bdata in brokers.items():
        for broker_id,net_val in bdata.items():
            rows.append((sym,date_str,str(broker_id),float(net_val)))
    if rows:
        sql=chr(73)+chr(78)+chr(83)+chr(69)+chr(82)+chr(84)+chr(32)+chr(79)+chr(82)+chr(32)+chr(73)+chr(71)+chr(78)+chr(79)+chr(82)+chr(69)+chr(32)+chr(73)+chr(78)+chr(84)+chr(79)+chr(32)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(97)+chr(99)+chr(116)+chr(105)+chr(118)+chr(105)+chr(116)+chr(121)+chr(32)+chr(40)+chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)+chr(44)+chr(100)+chr(97)+chr(116)+chr(101)+chr(44)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(44)+chr(110)+chr(101)+chr(116)+chr(95)+chr(118)+chr(97)+chr(108)+chr(41)+chr(32)+chr(86)+chr(65)+chr(76)+chr(85)+chr(69)+chr(83)+chr(32)+chr(40)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(41)
        conn.executemany(sql,rows)
        conn.commit()
        print(chr(32)+chr(32)+chr(73)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(101)+chr(100),date_str,chr(45),len(rows),chr(114)+chr(111)+chr(119)+chr(115))
        return True
    return False

def ensure_table(conn):
    sql=chr(67)+chr(82)+chr(69)+chr(65)+chr(84)+chr(69)+chr(32)+chr(84)+chr(65)+chr(66)+chr(76)+chr(69)+chr(32)+chr(73)+chr(70)+chr(32)+chr(78)+chr(79)+chr(84)+chr(32)+chr(69)+chr(88)+chr(73)+chr(83)+chr(84)+chr(83)+chr(32)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(97)+chr(99)+chr(116)+chr(105)+chr(118)+chr(105)+chr(116)+chr(121)+chr(32)+chr(40)+chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(100)+chr(97)+chr(116)+chr(101)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(110)+chr(101)+chr(116)+chr(95)+chr(118)+chr(97)+chr(108)+chr(32)+chr(82)+chr(69)+chr(65)+chr(76)+chr(44)+chr(32)+chr(85)+chr(78)+chr(73)+chr(81)+chr(85)+chr(69)+chr(32)+chr(40)+chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)+chr(44)+chr(100)+chr(97)+chr(116)+chr(101)+chr(44)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(41)+chr(41)
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
        print(chr(67)+chr(108)+chr(101)+chr(97)+chr(110)+chr(101)+chr(100)+chr(32)+chr(117)+chr(112),len(to_delete),chr(102)+chr(105)+chr(108)+chr(101)+chr(115)+chr(32)+chr(40)+chr(49)+chr(32)+chr(121)+chr(114)+chr(32)+chr(111)+chr(108)+chr(100)+chr(41))
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
    print(chr(80)+chr(117)+chr(108)+chr(108)+chr(105)+chr(110)+chr(103)+chr(32)+chr(108)+chr(97)+chr(116)+chr(101)+chr(115)+chr(116)+chr(32)+chr(100)+chr(97)+chr(116)+chr(97)+chr(32)+chr(102)+chr(114)+chr(111)+chr(109)+chr(32)+chr(71)+chr(105)+chr(116)+chr(72)+chr(117)+chr(98)+chr(46)+chr(46)+chr(46))
    git_pull()
    if not os.path.isdir(DATA_DIR):
        print(chr(78)+chr(111)+chr(32)+chr(100)+chr(97)+chr(105)+chr(108)+chr(121)+chr(95)+chr(100)+chr(97)+chr(116)+chr(97)+chr(32)+chr(102)+chr(111)+chr(108)+chr(100)+chr(101)+chr(114)+chr(32)+chr(121)+chr(101)+chr(116))
        return
    conn=sqlite3.connect(DB)
    ensure_table(conn)
    imported=get_imported_dates(conn)
    log=load_log()
    files=sorted(f for f in os.listdir(DATA_DIR) if f.startswith(chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)) and f.endswith(chr(46)+chr(106)+chr(115)+chr(111)+chr(110)))
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

    if new_count: print(chr(73)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(101)+chr(100),new_count,chr(110)+chr(101)+chr(119)+chr(32)+chr(100)+chr(97)+chr(121)+chr(115))
    else: print(chr(68)+chr(66)+chr(32)+chr(117)+chr(112)+chr(32)+chr(116)+chr(111)+chr(32)+chr(100)+chr(97)+chr(116)+chr(101)+chr(32)+chr(45)+chr(32)+chr(110)+chr(111)+chr(32)+chr(110)+chr(101)+chr(119)+chr(32)+chr(100)+chr(97)+chr(116)+chr(97))
    cleanup_old_files(log)

if __name__==chr(95)+chr(95)+chr(109)+chr(97)+chr(105)+chr(110)+chr(95)+chr(95):
    main()
