src = open("nepse_alerts.py", encoding="utf-8").read()

old = '''        # \u2500\u2500 Alert 4: POWER SELL (watchlist only) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        if in_wl and chg <= POWER_SELL_DROP and can_alert(f"{sym}_powersell"):
            msg = (
                f"<b>NEPSE ALERT \u2014 {now_str}</b>\\n\\n"
                f"<b>POWER SELL WARNING: {sym}</b>\\n"
                f"Your watchlist stock dropping {chg:.2f}% today\\n"
                f"LTP: Rs {ltp:,.1f} | Vol: {vol/1000:.0f}K\\n"
                f"<i>Check if smart money is exiting</i>"
            )
            if send_telegram(msg):
                log.info(f"POWER SELL alert: {sym}")
                alerts_sent += 1
    log.info(f"Alert check complete \u2014 {alerts_sent} alerts sent")
    return alerts_sent'''

new = old.replace(
    "    log.info(f\"Alert check complete \u2014 {alerts_sent} alerts sent\")\n    return alerts_sent",
    """
        # \u2500\u2500 Alert 5: WHALE ALERT \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        if avg_vol > 0:
            vol_mult = vol / avg_vol
            if vol_mult >= 5.0 and turnover >= 5_000_000 and can_alert(f"{sym}_whale"):
                wl_tag = " | IN YOUR WATCHLIST" if in_wl else ""
                direction = "BUYING" if chg >= 0 else "SELLING"
                msg = (
                    f"<b>NEPSE ALERT \u2014 {now_str}</b>\\\\n\\\\n"
                    f"<b>WHALE ALERT: {sym}</b>{wl_tag}\\\\n"
                    f"Volume <b>{vol_mult:.1f}x</b> above 20D avg\\\\n"
                    f"Turnover: Rs {turnover/1e6:.1f}M | Direction: {direction}\\\\n"
                    f"LTP: Rs {ltp:,.1f} | Change: {chg:+.2f}%\\\\n"
                    f"<i>Institutional activity detected</i>"
                )
                if send_telegram(msg):
                    log.info(f"WHALE alert: {sym}")
                    alerts_sent += 1

    log.info(f"Alert check complete \u2014 {alerts_sent} alerts sent")
    return alerts_sent"""
)

if old in src:
    new_src = src.replace(old, new)
    open("nepse_alerts.py", "w", encoding="utf-8").write(new_src)
    print("OK - Whale alert added")
else:
    # Direct injection approach
    target = '    log.info(f"Alert check complete'
    whale_block = '''
        # -- Alert 5: WHALE ALERT --
        if avg_vol > 0:
            vol_mult = vol / avg_vol
            if vol_mult >= 5.0 and turnover >= 5_000_000 and can_alert(f"{sym}_whale"):
                wl_tag = " | IN YOUR WATCHLIST" if in_wl else ""
                direction = "BUYING" if chg >= 0 else "SELLING"
                msg = (
                    f"<b>NEPSE ALERT - {now_str}</b>\\n\\n"
                    f"<b>WHALE ALERT: {sym}</b>{wl_tag}\\n"
                    f"Volume <b>{vol_mult:.1f}x</b> above 20D avg\\n"
                    f"Turnover: Rs {turnover/1e6:.1f}M | Direction: {direction}\\n"
                    f"LTP: Rs {ltp:,.1f} | Change: {chg:+.2f}%\\n"
                    f"<i>Institutional activity detected</i>"
                )
                if send_telegram(msg):
                    log.info(f"WHALE alert: {sym}")
                    alerts_sent += 1

'''
    if target in src:
        new_src = src.replace(target, whale_block + target)
        open("nepse_alerts.py", "w", encoding="utf-8").write(new_src)
        print("OK - Whale alert injected")
    else:
        print("ERROR - could not find injection point")

# Verify
src2 = open("nepse_alerts.py", encoding="utf-8").read()
print("Whale in file:", "whale" in src2.lower())
