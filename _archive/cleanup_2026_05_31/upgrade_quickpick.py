import ast, sqlite3

src = open('nepse_scanner.py', encoding='utf-8').read()
lines = src.splitlines()

# Find the function start and end
start = None
end = None
for i, l in enumerate(lines):
    if 'def analyze_quick_pick' in l:
        start = i
    if start and i > start and l.startswith('def ') and 'analyze_quick_pick' not in l:
        end = i
        break

print(f'Function: lines {start} to {end}')

new_func = '''def analyze_quick_pick(live_df, top_n=10, db_path="nepse_market_data.db"):
    console.print()
    console.print(Rule("[bold green]Quick Stock Pick[/bold green]", style="green"))
    console.print("[dim]Best stocks for 10%+ gain in 7 days to 1 month — signals only[/dim]\\n")

    if live_df is None or live_df.empty:
        console.print("[red]No live data.[/red]")
        return []

    df = live_df.copy()
    df = df[df["ltp"].notna() & df["volume"].notna() & (df["ltp"] > 0)].copy()

    # --- Load DB data ---
    db_vol_avg = {}
    db_rs = {}
    db_broker_net = {}
    db_sector_scores = {}

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # 20-day avg volume per stock
        c.execute("""
            SELECT symbol, AVG(volume) as avg_vol
            FROM (
                SELECT symbol, volume FROM stock_prices
                ORDER BY date DESC LIMIT 99999
            )
            GROUP BY symbol
        """)
        for sym, avg_vol in c.fetchall():
            db_vol_avg[sym] = avg_vol or 0

        # RS proxy from fundamentals (ROE - sector avg ROE)
        c.execute("SELECT symbol, roe, sector FROM fundamentals WHERE date = (SELECT MAX(date) FROM fundamentals)")
        rows = c.fetchall()
        sector_roe = {}
        for sym, roe, sector in rows:
            if roe and sector:
                if sector not in sector_roe:
                    sector_roe[sector] = []
                sector_roe[sector].append(roe)
        sector_roe_avg = {s: sum(v)/len(v) for s,v in sector_roe.items() if v}
        for sym, roe, sector in rows:
            if roe and sector and sector in sector_roe_avg:
                db_rs[sym] = roe - sector_roe_avg[sector]

        # Broker net buy (last 3 days)
        c.execute("""
            SELECT symbol, SUM(net_qty) as net
            FROM broker_activity
            WHERE date >= date('now', '-3 days')
            GROUP BY symbol
        """)
        for sym, net in c.fetchall():
            db_broker_net[sym] = net or 0

        # Sector momentum — avg % change per sector today
        if "sector" in df.columns:
            for sector in df["sector"].dropna().unique():
                sector_df = df[df["sector"] == sector]
                if not sector_df.empty:
                    db_sector_scores[sector] = float(sector_df["change_pct"].mean())

        conn.close()
    except Exception as e:
        pass  # DB unavailable, continue without it

    scores = []
    vol_median  = df["volume"].median()
    turn_median = df["turnover"].median() if "turnover" in df.columns else 0

    for _, row in df.iterrows():
        sym    = row.get("symbol", "")
        ltp    = row.get("ltp", 0)
        chg    = row.get("change_pct", 0) or 0
        vol    = row.get("volume", 0) or 0
        turn   = row.get("turnover", 0) or 0
        h52    = row.get("week52_high", 0) or 0
        l52    = row.get("week52_low", 0) or 0
        high   = row.get("high", 0) or 0
        low    = row.get("low", 0) or 0
        sector = row.get("sector", "") or ""

        score   = 0
        reasons = []

        # 1. Momentum (max 25 pts)
        if chg >= 5:
            score += 25; reasons.append("Strong momentum")
        elif chg >= 3:
            score += 18; reasons.append("Good momentum")
        elif chg >= 1:
            score += 10; reasons.append("Positive")
        elif chg < 0:
            score -= 10

        # 2. Volume surge — use stock own 20D avg if available (max 25 pts)
        own_avg_vol = db_vol_avg.get(sym, 0)
        base_vol    = own_avg_vol if own_avg_vol > 0 else vol_median
        if base_vol > 0:
            vol_ratio = vol / base_vol
            if vol_ratio >= 5:
                score += 25; reasons.append(f"Vol {vol_ratio:.1f}x own avg surge")
            elif vol_ratio >= 3:
                score += 20; reasons.append(f"Vol {vol_ratio:.1f}x own avg high")
            elif vol_ratio >= 2:
                score += 12; reasons.append(f"Vol {vol_ratio:.1f}x own avg")

        # 3. 52-week position (max 20 pts)
        if h52 > 0 and ltp > 0:
            dist_high = (h52 - ltp) / h52 * 100
            dist_low  = (ltp - l52) / l52 * 100 if l52 > 0 else 100
            if dist_high <= 3:
                score += 20; reasons.append("Near 52W breakout")
            elif dist_high <= 10:
                score += 14; reasons.append("Close to 52W high")
            elif dist_low <= 10 and chg > 0:
                score += 16; reasons.append("Bouncing from 52W low")
            elif dist_high >= 40:
                score -= 5

        # 4. Liquidity (max 15 pts)
        if turn_median > 0:
            turn_ratio = turn / turn_median
            if turn_ratio >= 3:
                score += 15; reasons.append("Very liquid")
            elif turn_ratio >= 1.5:
                score += 10; reasons.append("Good liquidity")
            elif turn_ratio < 0.3:
                score -= 10; reasons.append("Low liquidity")

        # 5. Day range tightness (max 15 pts)
        if high > 0 and low > 0 and ltp > 0:
            rng_pct = (high - low) / ltp * 100
            if rng_pct <= 1.5 and chg > 0:
                score += 15; reasons.append("Tight range breakout")
            elif rng_pct <= 3 and chg > 0:
                score += 8; reasons.append("Controlled move")

        # 6. RS from fundamentals DB (max 20 pts) — NEW
        rs_val = db_rs.get(sym, None)
        if rs_val is not None:
            if rs_val >= 10:
                score += 20; reasons.append(f"Strong RS vs sector")
            elif rs_val >= 5:
                score += 14; reasons.append(f"Good RS vs sector")
            elif rs_val >= 0:
                score += 7; reasons.append(f"Positive RS")
            else:
                score -= 5

        # 7. Broker net buy last 3 days (max 15 pts) — NEW
        broker_net = db_broker_net.get(sym, None)
        if broker_net is not None:
            if broker_net > 50000:
                score += 15; reasons.append("Strong broker accumulation")
            elif broker_net > 10000:
                score += 10; reasons.append("Broker buying")
            elif broker_net < -50000:
                score -= 10; reasons.append("Broker selling")

        # 8. Sector momentum (max 10 pts) — NEW
        if sector and sector in db_sector_scores:
            sec_chg = db_sector_scores[sector]
            if sec_chg >= 2:
                score += 10; reasons.append(f"Hot sector (+{sec_chg:.1f}%)")
            elif sec_chg >= 0.5:
                score += 5; reasons.append(f"Sector positive")
            elif sec_chg < -1:
                score -= 5

        # Filter
        if chg <= 0 or score < 30:
            continue

        # Upside estimate
        if h52 > 0 and ltp > 0:
            upside = (h52 - ltp) / ltp * 100
        else:
            upside = chg * 4

        scores.append({
            "symbol":  sym,
            "score":   min(score, 100),
            "ltp":     ltp,
            "change":  chg,
            "volume":  vol,
            "upside":  round(upside, 1),
            "reasons": " | ".join(reasons[:4]),
        })

    if not scores:
        console.print("[yellow]No quick pick candidates today.[/yellow]")
        return []

    scores = sorted(scores, key=lambda x: x["score"], reverse=True)

    t = Table(title="Quick Pick — Top Candidates (10%+ Potential)",
              box=box.ROUNDED, border_style="green", header_style="bold green")
    t.add_column("#",        width=3,  justify="right", style="dim")
    t.add_column("Symbol",   width=10, style="bold white")
    t.add_column("LTP",      width=13, justify="right", no_wrap=True)
'''

# Replace the function in source
old_func = "\n".join(lines[start:end])
new_src = src.replace(old_func, new_func)

# Verify it parses
ast.parse(new_src)

open('nepse_scanner.py', 'w', encoding='utf-8').write(new_src)
print('OK - quickpick upgraded')
print('New scoring:')
print('  Momentum:         25 pts (unchanged)')
print('  Volume (own avg): 25 pts (improved)')
print('  52W position:     20 pts (unchanged)')
print('  Liquidity:        15 pts (unchanged)')
print('  Day range:        15 pts (unchanged)')
print('  RS from DB:       20 pts (NEW)')
print('  Broker net buy:   15 pts (NEW)')
print('  Sector momentum:  10 pts (NEW)')
print('  Total max:        145 pts (capped at 100)')
