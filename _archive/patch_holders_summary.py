import shutil, ast

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_summary.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

old = "    if holders:\n        top = holders[0]\n        console.print(f\"  Top holder: Broker {top['broker_id']} ({top['broker_name']}) — net {'+' if top['total_net']>=0 else ''}{round(top['total_net']/1e6,1)}M over {top['days_active']} days\", style='bold')\n    console.print()"

new = """    if holders:
        top = holders[0]
        console.print(f"  Top holder: Broker {top['broker_id']} ({top['broker_name']}) — net {'+' if top['total_net']>=0 else ''}{round(top['total_net']/1e6,1)}M over {top['days_active']} days", style='bold')
        console.print()
        # Smart summary for top 3 holders
        console.print("  [bold cyan]── Smart Summary ──[/bold cyan]")
        for h in holders[:3]:
            net = h['total_net']
            net_qty = h.get('net_qty', 0)
            avg_b = h.get('avg_buy_price', 0)
            avg_s = h.get('avg_sell_price', 0)
            days = h['days_active']
            name = h['broker_name']
            bid = h['broker_id']
            amt = ('Rs ' + str(round(abs(net)/1e6, 1)) + 'M') if abs(net) >= 1e6 else ('Rs ' + str(round(abs(net)/1e3)) + 'K')
            qty_str = f'{abs(net_qty):,}'
            if net > 0 and avg_b > 0 and avg_s > 0:
                if avg_b > avg_s:
                    msg = f"Broker {bid} ({name}) bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — buying HIGHER than selling, net accumulating {qty_str} shares worth {amt}"
                else:
                    msg = f"Broker {bid} ({name}) bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — selling HIGHER than buying, collecting profit while accumulating {qty_str} net shares ({amt})"
            elif net > 0 and avg_b > 0 and avg_s == 0:
                msg = f"Broker {bid} ({name}) only BUYING — no sells, accumulating {qty_str} shares at avg Rs {avg_b:,.1f} ({amt} invested)"
            elif net < 0 and avg_b > 0 and avg_s > 0:
                if avg_s > avg_b:
                    msg = f"Broker {bid} ({name}) bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — selling HIGHER than buying, distributing {qty_str} shares at profit"
                else:
                    msg = f"Broker {bid} ({name}) bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — selling LOWER than buying, exiting position at loss ({amt} distributed)"
            elif net < 0 and avg_s > 0 and avg_b == 0:
                msg = f"Broker {bid} ({name}) only SELLING — no buys, distributing {qty_str} shares at avg Rs {avg_s:,.1f} ({amt} out)"
            else:
                msg = f"Broker {bid} ({name}) — net {'+' if net>=0 else ''}{amt} over {days} days"
            col = 'green' if net >= 0 else 'red'
            console.print(f"  [{col}]• {msg}[/{col}]")
    console.print()"""

if old in content:
    content = content.replace(old, new)
    print('Added smart summary lines')
else:
    print('ERROR: summary anchor not found')
    exit()

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK — smart summary installed')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_summary.py', 'nepse_scanner.py')
    print('Backup restored')
