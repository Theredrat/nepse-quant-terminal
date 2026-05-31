import shutil, ast, re

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_all_verdicts.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

if 'ten_day_verdict' in content:
    print('Already patched — nothing to do')
    exit()

# Find and replace get_broker_story
match = re.search(r'\ndef get_broker_story\(', content)
if not match:
    print('ERROR: get_broker_story not found')
    exit()

func_start = match.start()
next_func = re.search(r'\ndef ', content[func_start + 1:])
func_end = func_start + 1 + next_func.start() if next_func else content.rfind('\nif __name__')
print(f'Found get_broker_story ({func_end - func_start} chars) — replacing')

lines = [
    '',
    'def get_broker_story(symbol, fs_df, db_path="nepse_market_data.db"):',
    '    import sqlite3',
    '    empty = dict(',
    '        dominant_broker_id=None, dominant_broker_name=None, dominant_pct=0,',
    '        dominant_action="neutral", dominant_net_val=0, concentration="low",',
    '        total_brokers=0, buy_brokers=0, sell_brokers=0,',
    '        history_days=0, history_summary="", history_action="unknown",',
    '        five_day_verdict="", ten_day_verdict="", twenty_day_verdict="",',
    '    )',
    '    try:',
    '        if fs_df is None or fs_df.empty:',
    '            return empty',
    '        sym_fs = fs_df[fs_df["symbol"] == symbol] if "symbol" in fs_df.columns else fs_df',
    '        if sym_fs.empty:',
    '            return empty',
    '        total_vol = sym_fs["quantity"].sum()',
    '        if total_vol == 0:',
    '            return empty',
    '        buy_grp = sym_fs.groupby("buyer_broker").agg(',
    '            bq=("quantity", "sum"), bv=("amount", "sum"), bname=("buyerBrokerName", "first")',
    '        )',
    '        sell_grp = sym_fs.groupby("seller_broker").agg(',
    '            sq=("quantity", "sum"), sv=("amount", "sum"), sname=("sellerBrokerName", "first")',
    '        )',
    '        all_ids = set(buy_grp.index) | set(sell_grp.index)',
    '        rows = []',
    '        for bid in all_ids:',
    '            bq = int(buy_grp.loc[bid, "bq"]) if bid in buy_grp.index else 0',
    '            bv = float(buy_grp.loc[bid, "bv"]) if bid in buy_grp.index else 0.0',
    '            sq = int(sell_grp.loc[bid, "sq"]) if bid in sell_grp.index else 0',
    '            sv = float(sell_grp.loc[bid, "sv"]) if bid in sell_grp.index else 0.0',
    '            name = str(buy_grp.loc[bid, "bname"] if bid in buy_grp.index else sell_grp.loc[bid, "sname"])',
    '            vol = bq + sq',
    '            rows.append(dict(bid=str(bid), name=name, bq=bq, bv=bv, sq=sq, sv=sv,',
    '                net_val=bv-sv, net_qty=bq-sq, vol=vol))',
    '        if not rows:',
    '            return empty',
    '        dom = max(rows, key=lambda r: r["vol"])',
    '        dom_pct = dom["vol"] / (total_vol * 2) * 100',
    '        conc = "high" if dom_pct >= 30 else ("medium" if dom_pct >= 15 else "low")',
    '        action = "buying" if dom["net_val"] > 0 else ("selling" if dom["net_val"] < 0 else "neutral")',
    '        buy_brokers = sum(1 for r in rows if r["net_val"] > 0)',
    '        sell_brokers = sum(1 for r in rows if r["net_val"] < 0)',
    '        history_days = 0',
    '        history_summary = ""',
    '        history_action = "unknown"',
    '        five_day_verdict = ""',
    '        ten_day_verdict = ""',
    '        twenty_day_verdict = ""',
    '        try:',
    '            conn = sqlite3.connect(db_path)',
    '            hist = conn.execute(',
    '                "SELECT date, net_val FROM broker_activity WHERE symbol=? AND broker_id=?"',
    '                " ORDER BY date DESC LIMIT 20",',
    '                (symbol, dom["bid"])',
    '            ).fetchall()',
    '            conn.close()',
    '            if len(hist) >= 2:',
    '                history_days = len(hist)',
    '                def _ws(days_slice):',
    '                    if not days_slice: return None',
    '                    n = len(days_slice)',
    '                    b = sum(1 for _, nv in days_slice if nv > 0)',
    '                    s = sum(1 for _, nv in days_slice if nv < 0)',
    '                    net = sum(nv for _, nv in days_slice)',
    '                    amt = ("Rs " + str(round(abs(net)/1e6, 1)) + "M") if abs(net) >= 1e6 else ("Rs " + str(round(abs(net)/1e3)) + "K")',
    '                    if b > s: return str(b) + "/" + str(n) + "d bought (" + amt + " in)"',
    '                    elif s > b: return str(s) + "/" + str(n) + "d sold (" + amt + " out)"',
    '                    else: return str(n) + "d mixed"',
    '                w5  = _ws(hist[:5])  if len(hist) >= 5  else None',
    '                w10 = _ws(hist[:10]) if len(hist) >= 10 else None',
    '                w20 = _ws(hist[:20]) if len(hist) >= 20 else None',
    '                parts = []',
    '                if w5:  parts.append("5d: " + w5)',
    '                if w10: parts.append("10d: " + w10)',
    '                if w20: parts.append("20d: " + w20)',
    '                history_summary = "  |  ".join(parts) if parts else ""',
    '                all_b = sum(1 for _, nv in hist if nv > 0)',
    '                all_s = sum(1 for _, nv in hist if nv < 0)',
    '                history_action = "accumulating" if all_b > all_s else ("distributing" if all_s > all_b else "mixed")',
    '                # 5d verdict',
    '                if len(hist) >= 5:',
    '                    h5 = hist[:5]',
    '                    b5 = sum(1 for _, nv in h5 if nv > 0)',
    '                    s5 = sum(1 for _, nv in h5 if nv < 0)',
    '                    n5 = sum(nv for _, nv in h5)',
    '                    a5 = ("Rs " + str(round(abs(n5)/1e6, 1)) + "M") if abs(n5) >= 1e6 else ("Rs " + str(round(abs(n5)/1e3)) + "K")',
    '                    if b5 >= 4:',
    '                        five_day_verdict = "EARLY BUY SIGNAL — broker bought " + str(b5) + "/5 days (" + a5 + " in) — watch closely"',
    '                    elif b5 == 3:',
    '                        five_day_verdict = "MILD INTEREST — broker bought 3/5 days (" + a5 + " in) — not confirmed yet"',
    '                    elif s5 >= 4:',
    '                        five_day_verdict = "EARLY SELL SIGNAL — broker sold " + str(s5) + "/5 days (" + a5 + " out) — caution"',
    '                    elif s5 == 3:',
    '                        five_day_verdict = "MILD EXIT — broker sold 3/5 days (" + a5 + " out) — monitor"',
    '                    else:',
    '                        five_day_verdict = "NO SIGNAL — broker direction unclear over 5 days"',
    '                # 10d verdict',
    '                if len(hist) >= 10:',
    '                    h10 = hist[:10]',
    '                    b10 = sum(1 for _, nv in h10 if nv > 0)',
    '                    s10 = sum(1 for _, nv in h10 if nv < 0)',
    '                    n10 = sum(nv for _, nv in h10)',
    '                    a10 = ("Rs " + str(round(abs(n10)/1e6, 1)) + "M") if abs(n10) >= 1e6 else ("Rs " + str(round(abs(n10)/1e3)) + "K")',
    '                    if b10 >= 8:',
    '                        ten_day_verdict = "STRONG BUY — broker bought " + str(b10) + "/10 days (" + a10 + " accumulated) — high conviction"',
    '                    elif b10 >= 6:',
    '                        ten_day_verdict = "MODERATE BUY — broker bought " + str(b10) + "/10 days (" + a10 + " in) — building position"',
    '                    elif s10 >= 8:',
    '                        ten_day_verdict = "STRONG AVOID — broker sold " + str(s10) + "/10 days (" + a10 + " distributed) — consistent exit"',
    '                    elif s10 >= 6:',
    '                        ten_day_verdict = "CAUTION — broker sold " + str(s10) + "/10 days (" + a10 + " out) — distribution ongoing"',
    '                    else:',
    '                        ten_day_verdict = "NO CONVICTION — broker mixed over 10 days (bought " + str(b10) + ", sold " + str(s10) + ")"',
    '                # 20d verdict',
    '                if len(hist) >= 20:',
    '                    h20 = hist[:20]',
    '                    b20 = sum(1 for _, nv in h20 if nv > 0)',
    '                    s20 = sum(1 for _, nv in h20 if nv < 0)',
    '                    n20 = sum(nv for _, nv in h20)',
    '                    a20 = ("Rs " + str(round(abs(n20)/1e6, 1)) + "M") if abs(n20) >= 1e6 else ("Rs " + str(round(abs(n20)/1e3)) + "K")',
    '                    if b20 >= 16:',
    '                        twenty_day_verdict = "INSTITUTIONAL ACCUMULATION — broker bought " + str(b20) + "/20 days (" + a20 + " in) — very high conviction"',
    '                    elif b20 >= 12:',
    '                        twenty_day_verdict = "STRONG ACCUMULATION — broker bought " + str(b20) + "/20 days (" + a20 + " in) — sustained buying"',
    '                    elif b20 >= 8:',
    '                        twenty_day_verdict = "MODERATE ACCUMULATION — broker bought " + str(b20) + "/20 days (" + a20 + " in) — mild interest"',
    '                    elif s20 >= 16:',
    '                        twenty_day_verdict = "INSTITUTIONAL DISTRIBUTION — broker sold " + str(s20) + "/20 days (" + a20 + " out) — major exit"',
    '                    elif s20 >= 12:',
    '                        twenty_day_verdict = "STRONG DISTRIBUTION — broker sold " + str(s20) + "/20 days (" + a20 + " out) — sustained selling"',
    '                    elif s20 >= 8:',
    '                        twenty_day_verdict = "MODERATE DISTRIBUTION — broker sold " + str(s20) + "/20 days (" + a20 + " out) — mild exit"',
    '                    else:',
    '                        twenty_day_verdict = "NO TREND — no clear direction over 20 days (bought " + str(b20) + ", sold " + str(s20) + ")"',
    '        except Exception:',
    '            pass',
    '        return dict(',
    '            dominant_broker_id=dom["bid"],',
    '            dominant_broker_name=dom["name"],',
    '            dominant_pct=dom_pct,',
    '            dominant_action=action,',
    '            dominant_net_val=dom["net_val"],',
    '            concentration=conc,',
    '            total_brokers=len(rows),',
    '            buy_brokers=buy_brokers,',
    '            sell_brokers=sell_brokers,',
    '            history_days=history_days,',
    '            history_summary=history_summary,',
    '            history_action=history_action,',
    '            five_day_verdict=five_day_verdict,',
    '            ten_day_verdict=ten_day_verdict,',
    '            twenty_day_verdict=twenty_day_verdict,',
    '        )',
    '    except Exception:',
    '        return empty',
    '',
]

NEW_FUNC = '\n' + '\n'.join(lines) + '\n'
content = content[:func_start] + NEW_FUNC + content[func_end:]

# Wire all three verdicts into _print_why after the reversal alert lines
old_wire = "            if bstory['history_action'] == 'distributing' and bstory['dominant_action'] == 'buying':\n                    hist_note += \" ← FIRST BUY after distribution (reversal alert)\""
new_wire = """            if bstory['history_action'] == 'distributing' and bstory['dominant_action'] == 'buying':
                    hist_note += " ← FIRST BUY after distribution (reversal alert)"
            if bstory.get('five_day_verdict'):
                    hist_note += "\\n      📊 5D:  " + bstory['five_day_verdict']
            if bstory.get('ten_day_verdict'):
                    hist_note += "\\n      ⭐ 10D: " + bstory['ten_day_verdict']
            if bstory.get('twenty_day_verdict'):
                    hist_note += "\\n      🏆 20D: " + bstory['twenty_day_verdict']"""

if old_wire in content:
    content = content.replace(old_wire, new_wire)
    print('Wired 5d/10d/20d verdicts into _print_why')
else:
    print('WARNING: _print_why wire point not found — verdicts calculated but not displayed')

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK — 5d/10d/20d verdicts all installed')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_all_verdicts.py', 'nepse_scanner.py')
    print('Backup restored')
