import shutil, ast, re

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_shares.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

# Update get_top_broker_holders to also fetch qty data
old_sql = (
    "        rows = conn.execute(\n"
    "            'SELECT broker_id, broker_name, '\n"
    "            'SUM(buy_val) as total_buy, SUM(sell_val) as total_sell, '\n"
    "            'SUM(net_val) as total_net, COUNT(DISTINCT date) as days_active '\n"
    "            'FROM broker_activity WHERE symbol=? '\n"
    "            'GROUP BY broker_id, broker_name '\n"
    "            'ORDER BY total_net DESC',\n"
    "            (symbol,)\n"
    "        ).fetchall()"
)
new_sql = (
    "        rows = conn.execute(\n"
    "            'SELECT broker_id, broker_name, '\n"
    "            'SUM(buy_val) as total_buy, SUM(sell_val) as total_sell, '\n"
    "            'SUM(net_val) as total_net, COUNT(DISTINCT date) as days_active, '\n"
    "            'SUM(buy_qty) as total_buy_qty, SUM(sell_qty) as total_sell_qty '\n"
    "            'FROM broker_activity WHERE symbol=? '\n"
    "            'GROUP BY broker_id, broker_name '\n"
    "            'ORDER BY total_net DESC',\n"
    "            (symbol,)\n"
    "        ).fetchall()"
)

if old_sql in content:
    content = content.replace(old_sql, new_sql)
    print('Updated SQL to include qty data')
else:
    print('ERROR: SQL not found')
    exit()

# Update the results parsing to include qty and avg price
old_parse = (
    "        for bid, bname, tbuy, tsell, tnet, days in rows:\n"
    "            results.append(dict(\n"
    "                broker_id=str(bid),\n"
    "                broker_name=str(bname or ''),\n"
    "                total_buy=float(tbuy or 0),\n"
    "                total_sell=float(tsell or 0),\n"
    "                total_net=float(tnet or 0),\n"
    "                days_active=int(days or 0),\n"
    "            ))"
)
new_parse = (
    "        for bid, bname, tbuy, tsell, tnet, days, bqty, sqty in rows:\n"
    "            tbuy = float(tbuy or 0)\n"
    "            tsell = float(tsell or 0)\n"
    "            bqty = int(bqty or 0)\n"
    "            sqty = int(sqty or 0)\n"
    "            avg_buy = round(tbuy / bqty, 2) if bqty > 0 else 0\n"
    "            avg_sell = round(tsell / sqty, 2) if sqty > 0 else 0\n"
    "            results.append(dict(\n"
    "                broker_id=str(bid),\n"
    "                broker_name=str(bname or ''),\n"
    "                total_buy=tbuy,\n"
    "                total_sell=tsell,\n"
    "                total_net=float(tnet or 0),\n"
    "                days_active=int(days or 0),\n"
    "                total_buy_qty=bqty,\n"
    "                total_sell_qty=sqty,\n"
    "                net_qty=bqty-sqty,\n"
    "                avg_buy_price=avg_buy,\n"
    "                avg_sell_price=avg_sell,\n"
    "            ))"
)

if old_parse in content:
    content = content.replace(old_parse, new_parse)
    print('Updated results parsing with qty and avg price')
else:
    print('ERROR: results parsing not found')
    exit()

# Update analyze_broker_holders table to show shares and avg price
old_table = (
    "    t.add_column('#', style='dim', width=4)\n"
    "    t.add_column('Broker ID', width=10)\n"
    "    t.add_column('Broker Name', width=35)\n"
    "    t.add_column('Net Position', width=16, justify='right')\n"
    "    t.add_column('Total Bought', width=16, justify='right')\n"
    "    t.add_column('Total Sold', width=16, justify='right')\n"
    "    t.add_column('Days Active', width=12, justify='right')"
)
new_table = (
    "    t.add_column('#', style='dim', width=4)\n"
    "    t.add_column('Broker ID', width=10)\n"
    "    t.add_column('Broker Name', width=32)\n"
    "    t.add_column('Net Position', width=14, justify='right')\n"
    "    t.add_column('Net Shares', width=12, justify='right')\n"
    "    t.add_column('Avg Buy', width=10, justify='right')\n"
    "    t.add_column('Avg Sell', width=10, justify='right')\n"
    "    t.add_column('Total Bought', width=14, justify='right')\n"
    "    t.add_column('Total Sold', width=14, justify='right')\n"
    "    t.add_column('Days', width=6, justify='right')"
)

if old_table in content:
    content = content.replace(old_table, new_table)
    print('Updated table columns')
else:
    print('ERROR: table columns not found')
    exit()

# Update the row rendering
old_row = (
    "        t.add_row(\n"
    "            str(i),\n"
    "            h['broker_id'],\n"
    "            h['broker_name'],\n"
    "            f'[{net_style}]{net_str}[/{net_style}]',\n"
    "            _fmt(h['total_buy']),\n"
    "            _fmt(h['total_sell']),\n"
    "            str(h['days_active']) + 'd',\n"
    "        )"
)
new_row = (
    "        net_qty = h.get('net_qty', 0)\n"
    "        nq_str = ('+' if net_qty >= 0 else '') + f'{net_qty:,}'\n"
    "        nq_style = 'green' if net_qty >= 0 else 'red'\n"
    "        avg_b = f\"Rs {h.get('avg_buy_price',0):,.1f}\" if h.get('avg_buy_price') else '-'\n"
    "        avg_s = f\"Rs {h.get('avg_sell_price',0):,.1f}\" if h.get('avg_sell_price') else '-'\n"
    "        t.add_row(\n"
    "            str(i),\n"
    "            h['broker_id'],\n"
    "            h['broker_name'],\n"
    "            f'[{net_style}]{net_str}[/{net_style}]',\n"
    "            f'[{nq_style}]{nq_str}[/{nq_style}]',\n"
    "            avg_b,\n"
    "            avg_s,\n"
    "            _fmt(h['total_buy']),\n"
    "            _fmt(h['total_sell']),\n"
    "            str(h['days_active']),\n"
    "        )"
)

if old_row in content:
    content = content.replace(old_row, new_row)
    print('Updated row rendering with shares and avg price')
else:
    print('ERROR: row rendering not found')
    exit()

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK — shares and avg price added to broker holders')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_shares.py', 'nepse_scanner.py')
    print('Backup restored')
