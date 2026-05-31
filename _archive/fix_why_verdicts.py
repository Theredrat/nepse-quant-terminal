import shutil
shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_why_fix.py')
content = open('nepse_scanner.py', encoding='utf-8').read()

# Fix 1: Filter lock-in dates > 6 months away (not relevant)
old1 = """        if unlock:
            parts.append(f"Lock-in expiry: {unlock} — supply overhang risk")
        else:
            parts.append("No lock-in expiry found")"""

new1 = """        if unlock:
            from datetime import datetime, date
            try:
                unlock_dt = datetime.strptime(unlock, '%Y-%m-%d').date()
                days_away = (unlock_dt - date.today()).days
                if days_away <= 180:
                    parts.append(f"Lock-in expiry: {unlock} ({days_away} days away) — supply overhang risk")
                else:
                    parts.append(f"No near-term lock-in expiry (next: {unlock})")
            except Exception:
                parts.append(f"Lock-in expiry: {unlock} — supply overhang risk")
        else:
            parts.append("No lock-in expiry found")"""

if old1 in content:
    content = content.replace(old1, new1)
    print('Fix 1 applied: lock-in filter > 6 months')
else:
    print('Fix 1 not found')

# Fix 2: Catch bull stock where dominant broker is actually selling (conflict signal)
old2 = """        if tag == 'bull':
            if bstory['history_action'] == 'accumulating' and rs5 > 5:
                verdict = "Sustained institutional accumulation + top RS. High conviction — buy on dips."
            elif da == 'buying' and bstory['concentration'] == 'high' and rs5 > 3:
                verdict = "Whale accumulating aggressively + strong RS. Watch for 52W high breakout."
            elif rs5 > 5:
                verdict = "Strongest momentum in market. Sector tailwind confirmed. Buy pullbacks."
            else:
                verdict = "Outperforming sector. Positive momentum — monitor for continuation." """

new2 = """        if tag == 'bull':
            if da == 'selling' and bstory['concentration'] in ('high','medium') and rs5 > 0:
                verdict = f"Strong RS but dominant broker net SELLING — possible distribution at highs. Wait for broker to stop selling before entry."
            elif bstory['history_action'] == 'accumulating' and rs5 > 5:
                verdict = "Sustained institutional accumulation + top RS. High conviction — buy on dips."
            elif da == 'buying' and bstory['concentration'] == 'high' and rs5 > 3:
                verdict = "Whale accumulating aggressively + strong RS. Watch for 52W high breakout."
            elif rs5 > 5:
                verdict = "Strongest momentum in market. Sector tailwind confirmed. Buy pullbacks."
            else:
                verdict = "Outperforming sector. Positive momentum — monitor for continuation." """

if old2 in content:
    content = content.replace(old2, new2)
    print('Fix 2 applied: bull+selling conflict detection')
else:
    print('Fix 2 not found')

# Fix 3: For bearish, if broad buying contradicts dominant seller — show the conflict
old3 = """            elif da == 'selling' and sec5 > 0:
                verdict = "Promoter/whale exit while sector rises. Stock-specific. Avoid until selling stops." """

new3 = """            elif da == 'selling' and sec5 > 0:
                buy_pct = bstory['buy_brokers'] / bstory['total_brokers'] * 100 if bstory['total_brokers'] > 0 else 0
                if buy_pct > 60:
                    verdict = "One whale selling while 60%+ brokers buying — possible shakeout before move up. Watch closely."
                else:
                    verdict = "Promoter/whale exit while sector rises. Stock-specific. Avoid until selling stops." """

if old3 in content:
    content = content.replace(old3, new3)
    print('Fix 3 applied: broad buying vs single seller conflict')
else:
    print('Fix 3 not found')

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)
print('Done.')
