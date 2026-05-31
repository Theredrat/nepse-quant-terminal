def auto_update_watchlist(rs_data, full_fs, db_path, top_n=15, silent=False):
    import sqlite3, json
    from pathlib import Path
    from collections import defaultdict

    try:
        conn = sqlite3.connect(db_path)
    except Exception as e:
        if not silent: print('Watchlist: DB error', e)
        return

    # RS scores
    if not rs_data:
        try: rs_data = _calc_relative_strength(db_path)
        except: rs_data = []
    rs_map = {r['symbol']: r for r in (rs_data or [])}

    # Fundamentals
    fund_map = {}
    try:
        for row in conn.execute('SELECT symbol, pe_ratio, pb_ratio, roe FROM fundamentals').fetchall():
            fund_map[row[0]] = {'pe': row[1] or 0, 'pb': row[2] or 0, 'roe': row[3] or 0}
    except: pass

    # EPS growth QoQ
    eps_growth_map = {}
    try:
        fy = conn.execute('SELECT MAX(fiscal_year) FROM quarterly_earnings').fetchone()[0]
        if fy:
            rows = conn.execute(
                'SELECT symbol, quarter, eps FROM quarterly_earnings WHERE fiscal_year=? ORDER BY symbol, quarter',
                (fy,)
            ).fetchall()
            eq = defaultdict(list)
            for sym, q, eps in rows:
                eq[sym].append(eps or 0)
            for sym, eps_list in eq.items():
                if len(eps_list) >= 2 and eps_list[-2] != 0:
                    eps_growth_map[sym] = (eps_list[-1] - eps_list[-2]) / abs(eps_list[-2]) * 100
    except: pass

    # Broker net activity
    broker_map = {}
    try:
        latest = conn.execute('SELECT MAX(date) FROM broker_activity').fetchone()[0]
        if latest:
            rows = conn.execute(
                'SELECT symbol, SUM(net_qty), SUM(net_val) FROM broker_activity WHERE date=? GROUP BY symbol',
                (latest,)
            ).fetchall()
            all_vals = sorted([abs(r[2] or 0) for r in rows], reverse=True)
            threshold = all_vals[int(len(all_vals) * 0.2)] if len(all_vals) > 5 else 0
            for sym, net_qty, net_val in rows:
                nq = net_qty or 0
                nv = net_val or 0
                broker_map[sym] = {'net_qty': nq, 'net_val': nv, 'top20': abs(nv) >= threshold and nv > 0}
    except: pass

    # Volume spike vs 20d avg
    vol_map = {}
    try:
        latest_price = conn.execute('SELECT MAX(date) FROM stock_prices').fetchone()[0]
        if latest_price:
            cur_vol = {r[0]: r[1] for r in conn.execute(
                'SELECT symbol, volume FROM stock_prices WHERE date=?', (latest_price,)
            ).fetchall()}
            avg_vol = {r[0]: r[1] for r in conn.execute(
                'SELECT symbol, AVG(volume) FROM stock_prices WHERE date >= date(?, "-20 days") GROUP BY symbol',
                (latest_price,)
            ).fetchall()}
            for sym, vol in cur_vol.items():
                avg = avg_vol.get(sym) or 0
                vol_map[sym] = {'spike': (vol or 0) > avg * 1.5 if avg > 0 else False}
    except: pass

    conn.close()

    # Score every symbol
    all_syms = set(list(rs_map.keys()) + list(fund_map.keys()) + list(broker_map.keys()))
    scores = {}
    for sym in all_syms:
        sc = 0
        rs = rs_map.get(sym, {})
        rs5  = rs.get('rs5',  0) or 0
        rs10 = rs.get('rs10', 0) or 0
        rs20 = rs.get('rs20', 0) or 0
        if rs5  > 5:  sc += 20
        elif rs5 > 2: sc += 10
        if rs10 > 3:  sc += 10
        elif rs10 > 1: sc += 5
        if rs20 > 2:  sc += 5

        bk = broker_map.get(sym, {})
        if bk.get('net_qty', 0) > 0: sc += 10
        if bk.get('top20', False):   sc += 5

        if vol_map.get(sym, {}).get('spike', False): sc += 10

        fn = fund_map.get(sym, {})
        roe = fn.get('roe', 0) or 0
        pe  = fn.get('pe',  0) or 0
        pb  = fn.get('pb',  0) or 0
        if roe > 15:  sc += 10
        elif roe > 8: sc += 5
        if 0 < pe < 15:   sc += 8
        elif 0 < pe < 30: sc += 4
        if 0 < pb < 3:    sc += 5

        eg = eps_growth_map.get(sym)
        if eg is not None:
            if eg > 20:   sc += 12
            elif eg > 10: sc += 7
            elif eg > 0:  sc += 3

        if sc > 0:
            scores[sym] = sc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top = [sym for sym, sc in ranked][:top_n]

    if not top:
        if not silent: print('Watchlist: no candidates found')
        return

    WL_PATH = Path('data/runtime/accounts/account_1/watchlist.json')
    watchlist = [
        {'kind': 'stock', 'key': 'stock:' + sym, 'label': sym, 'symbol': sym, 'score': scores.get(sym, 0)}
        for sym in top
    ]
    WL_PATH.parent.mkdir(parents=True, exist_ok=True)
    json.dump(watchlist, open(str(WL_PATH), 'w', encoding='utf-8'), indent=2)
    if not silent:
        print('Watchlist auto-updated ? top ' + str(len(top)) + ' by RS+Broker+Vol+ROE+EPS')
        if top: print('  Top: ' + ', '.join(top[:5]) + ('...' if len(top) > 5 else ''))
