import os, json, sqlite3, subprocess, datetime

DB = chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(95)+chr(100)+chr(97)+chr(116)+chr(97)+chr(46)+chr(100)+chr(98)
DATA_DIR = chr(100)+chr(97)+chr(105)+chr(108)+chr(121)+chr(95)+chr(100)+chr(97)+chr(116)+chr(97)

def git_pull():
    try:
        r = subprocess.run([chr(103)+chr(105)+chr(116), chr(112)+chr(117)+chr(108)+chr(108)], capture_output=True, text=True, timeout=30)
        print(chr(71)+chr(105)+chr(116)+chr(32)+chr(112)+chr(117)+chr(108)+chr(108)+chr(58), r.stdout.strip() or chr(79)+chr(75))
        return True
    except Exception as e:
        print(chr(71)+chr(105)+chr(116)+chr(32)+chr(112)+chr(117)+chr(108)+chr(108)+chr(32)+chr(102)+chr(97)+chr(105)+chr(108)+chr(101)+chr(100)+chr(58), e)
        return False

def get_imported_dates(conn):
    try:
        rows = conn.execute(chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(68)+chr(73)+chr(83)+chr(84)+chr(73)+chr(78)+chr(67)+chr(84)+chr(32)+chr(100)+chr(97)+chr(116)+chr(101)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(97)+chr(99)+chr(116)+chr(105)+chr(118)+chr(105)+chr(116)+chr(121)).fetchall()
        return set(r[0] for r in rows)
    except:
        return set()

def import_json(conn, path, date_str):
    data = json.load(open(path, encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)))
    brokers = data.get(chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(115), {})
    rows = []
    for sym, bdata in brokers.items():
        for broker_id, net_val in bdata.items():
            rows.append((sym, date_str, str(broker_id), float(net_val)))
    if rows:
        conn.executemany(chr(73)+chr(78)+chr(83)+chr(69)+chr(82)+chr(84)+chr(32)+chr(79)+chr(82)+chr(32)+chr(73)+chr(71)+chr(78)+chr(79)+chr(82)+chr(69)+chr(32)+chr(73)+chr(78)+chr(84)+chr(79)+chr(32)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(97)+chr(99)+chr(116)+chr(105)+chr(118)+chr(105)+chr(116)+chr(121)+chr(32)+chr(40)+chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)+chr(44)+chr(100)+chr(97)+chr(116)+chr(101)+chr(44)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(44)+chr(110)+chr(101)+chr(116)+chr(95)+chr(118)+chr(97)+chr(108)+chr(41)+chr(32)+chr(86)+chr(65)+chr(76)+chr(85)+chr(69)+chr(83)+chr(32)+chr(40)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(41), rows)
        conn.commit()
        print(chr(32)+chr(32)+chr(73)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(101)+chr(100)+chr(32), date_str, chr(45)+chr(32), len(rows), chr(114)+chr(111)+chr(119)+chr(115))
        return True
    return False

def ensure_table(conn):
    conn.execute(chr(67)+chr(82)+chr(69)+chr(65)+chr(84)+chr(69)+chr(32)+chr(84)+chr(65)+chr(66)+chr(76)+chr(69)+chr(32)+chr(73)+chr(70)+chr(32)+chr(78)+chr(79)+chr(84)+chr(32)+chr(69)+chr(88)+chr(73)+chr(83)+chr(84)+chr(83)+chr(32)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(97)+chr(99)+chr(116)+chr(105)+chr(118)+chr(105)+chr(116)+chr(121)+chr(32)+chr(40)+chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(100)+chr(97)+chr(116)+chr(101)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(110)+chr(101)+chr(116)+chr(95)+chr(118)+chr(97)+chr(108)+chr(32)+chr(82)+chr(69)+chr(65)+chr(76)+chr(44)+chr(32)+chr(85)+chr(78)+chr(73)+chr(81)+chr(85)+chr(69)+chr(32)+chr(40)+chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)+chr(44)+chr(100)+chr(97)+chr(116)+chr(101)+chr(44)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(41)+chr(41))
    conn.commit()

def main():
    print(chr(80)+chr(117)+chr(108)+chr(108)+chr(105)+chr(110)+chr(103)+chr(32)+chr(108)+chr(97)+chr(116)+chr(101)+chr(115)+chr(116)+chr(32)+chr(100)+chr(97)+chr(116)+chr(97)+chr(32)+chr(102)+chr(114)+chr(111)+chr(109)+chr(32)+chr(71)+chr(105)+chr(116)+chr(72)+chr(117)+chr(98)+chr(46)+chr(46)+chr(46))
    git_pull()
    if not os.path.isdir(DATA_DIR):
        print(chr(78)+chr(111)+chr(32)+chr(100)+chr(97)+chr(105)+chr(108)+chr(121)+chr(95)+chr(100)+chr(97)+chr(116)+chr(97)+chr(32)+chr(102)+chr(111)+chr(108)+chr(100)+chr(101)+chr(114)+chr(32)+chr(121)+chr(101)+chr(116)+chr(32)+chr(45)+chr(32)+chr(110)+chr(111)+chr(116)+chr(104)+chr(105)+chr(110)+chr(103)+chr(32)+chr(116)+chr(111)+chr(32)+chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116))
        return
    conn = sqlite3.connect(DB)
    ensure_table(conn)
    imported = get_imported_dates(conn)
    files = sorted(f for f in os.listdir(DATA_DIR) if f.startswith(chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)) and f.endswith(chr(46)+chr(106)+chr(115)+chr(111)+chr(110)))
    new_count = 0
    for fname in files:
        date_str = fname[7:17]
        if date_str in imported:
            continue
        path = os.path.join(DATA_DIR, fname)
        if import_json(conn, path, date_str):
            new_count += 1
    conn.close()
    if new_count:
        print(chr(73)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(101)+chr(100)+chr(32), new_count, chr(110)+chr(101)+chr(119)+chr(32)+chr(100)+chr(97)+chr(121)+chr(115)+chr(32)+chr(111)+chr(102)+chr(32)+chr(100)+chr(97)+chr(116)+chr(97))
    else:
        print(chr(68)+chr(66)+chr(32)+chr(117)+chr(112)+chr(32)+chr(116)+chr(111)+chr(32)+chr(100)+chr(97)+chr(116)+chr(101)+chr(32)+chr(45)+chr(32)+chr(110)+chr(111)+chr(32)+chr(110)+chr(101)+chr(119)+chr(32)+chr(100)+chr(97)+chr(116)+chr(97))

if __name__ == chr(95)+chr(95)+chr(109)+chr(97)+chr(105)+chr(110)+chr(95)+chr(95):
    main()
