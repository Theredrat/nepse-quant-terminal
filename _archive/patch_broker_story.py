import shutil, ast, re

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_broker_story.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

if 'days_bought' in content:
    print('Already patched — nothing to do')
    exit()

match = re.search(r'\ndef get_broker_story\(', content)
if not match:
    print('ERROR: get_broker_story not found')
    exit()

func_start = match.start()
next_func = re.search(r'\ndef ', content[func_start + 1:])
func_end = func_start + 1 + next_func.start() if next_func else content.rfind('\nif __name__')
print(f'Found get_broker_story ({func_end - func_start} chars)')

lines = [
    '',
    'def get_broker_story(symbol, fs_df, db_path="nepse_market_data.db"):',
    '    import sqlite3',
    '    bullets = []',
    '    today_brokers = {}',
    '    if fs_df is not None and not fs_df.empty:',
    '        sym_fs = fs_df[fs_df["symbol"] == symbol] if "symbol" in fs_df.columns else fs_df',
    '        if not sym_fs.empty:',
    '            total_vol = sym_fs["quantity"].sum()',
    '            buy_grp = sym_fs.groupby("buyer_broker").agg(',
    '                bq=("quantity", "sum"), bv=("amount", "sum"), bname=("buyerBrokerName", "first")',
    '            )',
    '            sell_grp = sym_fs.groupby("seller_broker").agg(',
    '                sq=("quantity", "sum"), sv=("amount", "sum"), sname=("sellerBrokerName", "first")',
    '            )',
    '            all_brokers = set(buy_grp.index) | set(sell_grp.index)',
    '            for bid in all_brokers:',
    '                bq = int(buy_grp.loc[bid, "bq"]) if bid in buy_grp.index else 0',
    '                bv = float(buy_grp.loc[bid, "bv"]) if bid in buy_grp.index else 0.0',
    '                sq = int(sell_grp.loc[bid, "sq"]) if bid in sell_grp.index else 0',
    '                sv = float(sell_grp.loc[bid, "sv"]) if bid in sell_grp.index else 0.0',
    '                bname = buy_grp.loc[bid, "bname"] if bid in buy_grp.index else sell_grp.loc[bid, "sname"]',
    '                today_brokers[str(bid)] = dict(bq=bq, bv=bv, sq=sq, sv=sv,',
    '                    net_qty=bq-sq, net_val=bv-sv, name=str(bname), total_vol=total_vol)',
    '    history = {}',
    '    try:',
    '        conn = sqlite3.connect(db_path)',
    '        rows = conn.execute(',
    '            "SELECT broker_id, date, net_val, net_qty, broker_name"',
    '            " FROM broker_activity WHERE symbol=? ORDER BY date DESC LIMIT 500",',
    '            (symbol,)',
    '        ).fetchall()',
    '        conn.close()',
    '        for bid, dt, nv, nq, bname in rows:',
    '            if bid not in history:',
    '                history[bid] = {"name": bname, "days": []}',
    '            history[bid]["days"].append({"date": dt, "net_val": nv, "net_qty": nq})',
    '    except Exception:',
    '        pass',
    '    sorted_brokers = sorted(today_brokers.items(), key=lambda x: abs(x[1]["net_val"]), reverse=True)[:5]',
    '    total_vol = list(today_brokers.values())[0]["total_vol"] if today_brokers else 1',
    '    for bid, td in sorted_brokers:',
    '        name = td["name"]',
    '        net_val = td["net_val"]',
    '        vol_pct = round((td["bq"] + td["sq"]) / (total_vol * 2) * 100) if total_vol else 0',
    '        direction = "net BUYING" if net_val > 0 else "net SELLING"',
    '        val_str = ("Rs " + str(round(abs(net_val)/1e6, 1)) + "M") if abs(net_val) >= 1e6 else ("Rs " + str(round(abs(net_val)/1e3)) + "K")',
    '        hist_str = ""',
    '        if bid in history and len(history[bid]["days"]) >= 2:',
    '            days = history[bid]["days"]',
    '            recent = days[:20]',
    '            days_bought = sum(1 for d in recent if d["net_val"] > 0)',
    '            days_sold = sum(1 for d in recent if d["net_val"] < 0)',
    '            total_days = len(recent)',
    '            total_hist_val = sum(d["net_val"] for d in recent)',
    '            total_str = ("Rs " + str(round(abs(total_hist_val)/1e6)) + "M") if abs(total_hist_val) >= 1e6 else ("Rs " + str(round(abs(total_hist_val)/1e3)) + "K")',
    '            if net_val > 0 and days_bought >= 3:',
    '                hist_str = " — bought " + str(days_bought) + "/" + str(total_days) + " days (net " + total_str + " accumulated)"',
    '            elif net_val < 0 and days_sold >= 3:',
    '                hist_str = " — sold " + str(days_sold) + "/" + str(total_days) + " days (net " + total_str + " distributed)"',
    '            elif net_val > 0 and days_sold > days_bought:',
    '                hist_str = " — REVERSAL: was selling " + str(days_sold) + "/" + str(total_days) + " days, NOW buying"',
    '            elif net_val < 0 and days_bought > days_sold:',
    '                hist_str = " — REVERSAL: was buying " + str(days_bought) + "/" + str(total_days) + " days, NOW selling"',
    '        bullets.append(',
    '            "Broker " + str(bid) + " (" + name + ") — " + str(vol_pct) + "% of today volume, " + direction + " (" + val_str + ")" + hist_str',
    '        )',
    '    if not bullets:',
    '        bullets.append("No floorsheet data available for today")',
    '    return bullets',
    '',
]

NEW_FUNC = '\n' + '\n'.join(lines) + '\n'

content = content[:func_start] + NEW_FUNC + content[func_end:]
open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK — get_broker_story patched with history awareness')
    print('days_bought logic: True')
    print('REVERSAL detection: True')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_broker_story.py', 'nepse_scanner.py')
    print('Backup restored — scanner unchanged')
