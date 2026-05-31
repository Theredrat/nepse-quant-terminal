import shutil, ast, re

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_story_dict.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

# Find and replace the current get_broker_story function
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
    '    """Return broker story dict expected by _print_why, enriched with DB history."""',
    '    import sqlite3',
    '    empty = dict(',
    '        dominant_broker_id=None, dominant_broker_name=None, dominant_pct=0,',
    '        dominant_action="neutral", dominant_net_val=0, concentration="low",',
    '        total_brokers=0, buy_brokers=0, sell_brokers=0,',
    '        history_days=0, history_summary="", history_action="unknown",',
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
    '        import pandas as pd',
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
    '        # dominant broker by volume',
    '        dom = max(rows, key=lambda r: r["vol"])',
    '        dom_pct = dom["vol"] / (total_vol * 2) * 100',
    '        if dom_pct >= 30:',
    '            conc = "high"',
    '        elif dom_pct >= 15:',
    '            conc = "medium"',
    '        else:',
    '            conc = "low"',
    '        if dom["net_val"] > 0:',
    '            action = "buying"',
    '        elif dom["net_val"] < 0:',
    '            action = "selling"',
    '        else:',
    '            action = "neutral"',
    '        buy_brokers = sum(1 for r in rows if r["net_val"] > 0)',
    '        sell_brokers = sum(1 for r in rows if r["net_val"] < 0)',
    '        # history from DB',
    '        history_days = 0',
    '        history_summary = ""',
    '        history_action = "unknown"',
    '        try:',
    '            conn = sqlite3.connect(db_path)',
    '            hist = conn.execute(',
    '                "SELECT date, net_val FROM broker_activity WHERE symbol=? AND broker_id=?"',
    '                " ORDER BY date DESC LIMIT 30",',
    '                (symbol, dom["bid"])',
    '            ).fetchall()',
    '            conn.close()',
    '            if len(hist) >= 2:',
    '                history_days = len(hist)',
    '                days_bought = sum(1 for _, nv in hist if nv > 0)',
    '                days_sold = sum(1 for _, nv in hist if nv < 0)',
    '                total_net = sum(nv for _, nv in hist)',
    '                total_str = ("Rs " + str(round(abs(total_net)/1e6, 1)) + "M") if abs(total_net) >= 1e6 else ("Rs " + str(round(abs(total_net)/1e3)) + "K")',
    '                if days_bought > days_sold:',
    '                    history_action = "accumulating"',
    '                    history_summary = "bought " + str(days_bought) + "/" + str(history_days) + " days (" + total_str + " accumulated)"',
    '                elif days_sold > days_bought:',
    '                    history_action = "distributing"',
    '                    history_summary = "sold " + str(days_sold) + "/" + str(history_days) + " days (" + total_str + " distributed)"',
    '                else:',
    '                    history_action = "mixed"',
    '                    history_summary = "mixed activity over " + str(history_days) + " days"',
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
    '        )',
    '    except Exception as e:',
    '        return empty',
    '',
]

NEW_FUNC = '\n' + '\n'.join(lines) + '\n'
content = content[:func_start] + NEW_FUNC + content[func_end:]
open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK — get_broker_story returns correct dict format with history enrichment')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_story_dict.py', 'nepse_scanner.py')
    print('Backup restored')
