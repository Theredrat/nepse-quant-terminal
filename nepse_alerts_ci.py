import os, time, logging, collections
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8926979126:AAFRdgGNAFDf_AouyqFOeXmc0FYC6ReE5GI")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT",  "1923100963")
RS_THRESHOLD   = 2.0
NEAR_HIGH_PCT  = 5.0
VOL_SPIKE_MULT = 3.0
POWER_SELL_PCT = -3.0
WATCHLIST = ["BHCL","BUNGAL","ALBSL","CREST","AKJCL","GRDBL","DHEL","GCIL","GBLBS","AVYAN","JBBL","BANDIPUR","HIDCL","GUFL","BHL"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

def send_telegram(msg):
    try:
        import requests
        r = requests.post(
            "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=10)
        return r.status_code == 200
    except Exception as e:
        log.error("Telegram error: " + str(e))
        return False

def get_nepse():
    from nepse import Nepse
    n = Nepse()
    n.setTLSVerification(False)
    return n

def get_live_data(n):
    try:
        import pandas as pd
        data = n.getLiveMarket()
        if data is None:
            return None
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        df = df.rename(columns={"lastTradedPrice":"ltp","percentageChange":"change_pct","totalTradeQuantity":"volume","totalTradeValue":"turnover"})
        for col in ["ltp","change_pct","volume","turnover"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
    except Exception as e:
        log.error("Live data error: " + str(e))
        return None

def get_sector_map(n):
    try:
        import pandas as pd
        data = n.getCompanyList()
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        if "symbol" in df.columns and "sectorName" in df.columns:
            return dict(zip(df["symbol"], df["sectorName"]))
        return {}
    except:
        return {}

def get_price_history(n, sym, days=365):
    try:
        import pandas as pd
        data = n.getCompanyPriceVolumeHistory(sym)
        if data is None:
            return None
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        if df.empty:
            return None
        for col in ["closePrice","close","lastTradedPrice"]:
            if col in df.columns:
                df = df.rename(columns={col:"close"})
                break
        if "close" not in df.columns:
            return None
        df["close"] = pd.to_numeric(df["close"], errors="coerce").fillna(0)
        return df[df["close"] > 0].tail(days)
    except:
        return None

def compute_rs(live, sector_map, n):
    import collections
    symbols = list(live.nlargest(80,"turnover")["symbol"].dropna().unique()) if "turnover" in live.columns else list(live["symbol"].dropna().unique())[:80]
    for sym in WATCHLIST:
        if sym not in symbols:
            symbols.append(sym)
    ret5_by_sector = collections.defaultdict(list)
    rs_score, week52, vol_med = {}, {}, {}
    log.info("Fetching history for " + str(len(symbols)) + " stocks...")
    for sym in symbols:
        try:
            hist = get_price_history(n, sym)
            if hist is None or len(hist) < 6:
                continue
            closes = hist["close"].values
            ret5 = (closes[-1] / closes[-6] - 1) * 100
            sector = sector_map.get(sym, "")
            rs_score[sym] = {"ret5": ret5, "sector": sector}
            week52[sym] = {"high52": float(hist["close"].max()), "sector": sector}
            if "volume" in hist.columns:
                vol_med[sym] = float(hist["volume"].median())
            ret5_by_sector[sector].append(ret5)
            time.sleep(0.1)
        except:
            pass
    sector_avg = {s: sum(v)/len(v) for s,v in ret5_by_sector.items() if v}
    rs_final = {sym: d["ret5"] - sector_avg.get(d["sector"],0) for sym,d in rs_score.items()}
    return rs_final, week52, vol_med, rs_score, sector_avg

def get_sector_rotation(live, sector_map):
    import collections
    sector_data = collections.defaultdict(lambda: {"up":0,"down":0,"flat":0,"total":0,"chg_sum":0.0})
    for _, row in live.iterrows():
        sym = str(row.get("symbol",""))
        chg = float(row.get("change_pct", 0))
        sector = sector_map.get(sym, "Others")
        if not sector:
            sector = "Others"
        sector_data[sector]["total"] += 1
        sector_data[sector]["chg_sum"] += chg
        if chg > 0.1:
            sector_data[sector]["up"] += 1
        elif chg < -0.1:
            sector_data[sector]["down"] += 1
        else:
            sector_data[sector]["flat"] += 1
    result = []
    for sector, d in sector_data.items():
        if d["total"] > 0:
            avg_chg = d["chg_sum"] / d["total"]
            result.append((sector, d["up"], d["down"], d["total"], avg_chg))
    result.sort(key=lambda x: -x[4])
    return result

def morning_briefing(live, rs_final, sector_map, rs_score, sector_avg):
    log.info("Sending morning briefing...")
    wl_count = str(len(WATCHLIST))
    lines = ["<b>🌅 NEPSE Morning Briefing</b>", ""]

    # Top 5 RS stocks
    top_rs = sorted(rs_final.items(), key=lambda x: -x[1])[:5]
    lines.append("<b>🔥 Top 5 RS Outperformers:</b>")
    for sym, rs in top_rs:
        sector = rs_score.get(sym, {}).get("sector", "")
        row = live[live["symbol"] == sym]
        ltp = int(float(row.iloc[0].get("ltp", 0))) if not row.empty else 0
        chg = float(row.iloc[0].get("change_pct", 0)) if not row.empty else 0
        arrow = "+" if chg >= 0 else ""
        lines.append("  <b>" + sym + "</b> RS +" + str(round(rs,1)) + "% | Rs " + str(ltp) + " (" + arrow + str(round(chg,1)) + "%) | " + sector)
    lines.append("")

    # Hottest sector
    if sector_avg:
        hottest = max(sector_avg.items(), key=lambda x: x[1])
        coldest = min(sector_avg.items(), key=lambda x: x[1])
        lines.append("<b>📊 Sector Pulse:</b>")
        lines.append("  🔥 Hottest: " + hottest[0] + " (+" + str(round(hottest[1],1)) + "% avg 5D)")
        lines.append("  ❄️ Coldest: " + coldest[0] + " (" + str(round(coldest[1],1)) + "% avg 5D)")
        lines.append("")

    # Watchlist
    lines.append("<b>📋 Watchlist (" + wl_count + " stocks):</b>")
    for sym in WATCHLIST:
        row = live[live["symbol"] == sym]
        if row.empty:
            lines.append("  " + sym + " - no data")
            continue
        ltp = float(row.iloc[0].get("ltp", 0))
        chg = float(row.iloc[0].get("change_pct", 0))
        rs5 = rs_final.get(sym, 0)
        score = 0
        if rs5 >= 5: score += 30
        elif rs5 >= 2: score += 20
        elif rs5 >= 0: score += 10
        if float(row.iloc[0].get("volume", 0)) > 0: score += 10
        if chg > 0: score += 5
        if score >= 35: reason = "Strong RS + Momentum"
        elif score >= 25: reason = "Good RS"
        elif score >= 15: reason = "Moderate signal"
        else: reason = "Monitor"
        arrow = "+" if chg >= 0 else ""
        lines.append("  <b>" + sym + "</b> Rs " + str(int(ltp)) + " (" + arrow + str(round(chg,1)) + "%) Score " + str(score) + " | " + reason)

    lines.append("")
    lines.append("<i>Alerts active. Good trading!</i>")
    send_telegram("\n".join(lines))

def eod_summary(live, sector_map):
    log.info("Sending EOD summary...")
    lines = ["<b>📉 NEPSE EOD Summary</b>", ""]

    # Sector rotation
    rotation = get_sector_rotation(live, sector_map)
    lines.append("<b>🔄 Sector Rotation Today:</b>")
    for sector, up, down, total, avg_chg in rotation[:6]:
        arrow = "▲" if avg_chg > 0 else "▼"
        pressure = "Buying" if up > down else "Selling"
        lines.append("  " + arrow + " " + sector + " " + str(round(avg_chg,1)) + "% | " + str(up) + "/" + str(total) + " up | " + pressure)
    lines.append("")

    # Watchlist gainers/losers
    gainers, losers, flat = [], [], []
    for sym in WATCHLIST:
        row = live[live["symbol"] == sym]
        if row.empty:
            continue
        ltp = float(row.iloc[0].get("ltp", 0))
        chg = float(row.iloc[0].get("change_pct", 0))
        vol = float(row.iloc[0].get("volume", 0))
        if chg > 0.1: gainers.append((sym, ltp, chg, vol))
        elif chg < -0.1: losers.append((sym, ltp, chg, vol))
        else: flat.append((sym, ltp, chg, vol))

    gainers.sort(key=lambda x: -x[2])
    losers.sort(key=lambda x: x[2])

    lines.append("<b>✅ Watchlist Gainers:</b>")
    for sym, ltp, chg, vol in gainers:
        lines.append("  " + sym + " +" + str(round(chg,1)) + "% | Rs " + str(int(ltp)) + " | Vol " + str(int(vol)))
    if not gainers:
        lines.append("  None")

    lines.append("")
    lines.append("<b>❌ Watchlist Losers:</b>")
    for sym, ltp, chg, vol in losers:
        lines.append("  " + sym + " " + str(round(chg,1)) + "% | Rs " + str(int(ltp)) + " | Vol " + str(int(vol)))
    if not losers:
        lines.append("  None")

    send_telegram("\n".join(lines))

def check_alerts(live, rs_final, week52, vol_med, sector_map):
    alerts_sent = 0
    now_str = datetime.now().strftime("%H:%M")
    wl_set = set(WATCHLIST)
    for _, row in live.iterrows():
        sym = str(row.get("symbol", ""))
        ltp = float(row.get("ltp", 0))
        chg = float(row.get("change_pct", 0))
        vol = float(row.get("volume", 0))
        turnover = float(row.get("turnover", 0))
        if not sym or ltp <= 0:
            continue
        rs5 = rs_final.get(sym, 0)
        high52 = week52.get(sym, {}).get("high52", 0)
        sector = sector_map.get(sym, "")
        med_vol = vol_med.get(sym, 0)
        in_wl = " | IN YOUR WATCHLIST" if sym in wl_set else ""
        if high52 > 0 and rs5 >= RS_THRESHOLD:
            pct_from_high = (ltp - high52) / high52 * 100
            if pct_from_high >= -NEAR_HIGH_PCT:
                stars = "***" if pct_from_high >= -1 else "**"
                msg = ("NEPSE ALERT - " + now_str + "\n\n" + stars + " BREAKOUT: " + sym + in_wl + "\n"
                    + "Near 52W High (" + str(round(pct_from_high,1)) + "%) + RS +" + str(round(rs5,1)) + "%\n"
                    + "LTP: Rs " + str(int(ltp)) + " | Change: " + str(round(chg,1)) + "%\n"
                    + "Turnover: Rs " + str(round(turnover/1e6,1)) + "M | Sector: " + sector)
                send_telegram(msg)
                log.info("BREAKOUT: " + sym)
                alerts_sent += 1
        if rs5 >= RS_THRESHOLD and med_vol > 0:
            vol_mult = vol / med_vol
            if vol_mult >= VOL_SPIKE_MULT:
                msg = ("NEPSE ALERT - " + now_str + "\n\nVOLUME SPIKE: " + sym + in_wl + "\n"
                    + "Volume " + str(round(vol_mult,1)) + "x above average\n"
                    + "RS: +" + str(round(rs5,1)) + "% | LTP: Rs " + str(int(ltp)) + " | Change: " + str(round(chg,1)) + "%\n"
                    + "Sector: " + sector)
                send_telegram(msg)
                log.info("VOL SPIKE: " + sym)
                alerts_sent += 1
        if rs5 >= RS_THRESHOLD and chg <= -3.0:
            msg = ("NEPSE ALERT - " + now_str + "\n\nRS REVERSAL: " + sym + in_wl + "\n"
                + "Was outperforming (RS +" + str(round(rs5,1)) + "%) but dropping " + str(round(chg,1)) + "% today\n"
                + "LTP: Rs " + str(int(ltp)) + " | Sector: " + sector)
            send_telegram(msg)
            log.info("REVERSAL: " + sym)
            alerts_sent += 1
        if sym in wl_set and chg <= POWER_SELL_PCT:
            msg = ("NEPSE ALERT - " + now_str + "\n\nPOWER SELL WARNING: " + sym + "\n"
                + "Your watchlist stock dropping " + str(round(chg,1)) + "% today\n"
                + "LTP: Rs " + str(int(ltp)) + " | Vol: " + str(int(vol)))
            send_telegram(msg)
            log.info("POWER SELL: " + sym)
            alerts_sent += 1
    return alerts_sent

def run():
    now = datetime.utcnow()
    hour = now.hour
    minute = now.minute
    log.info("CI alert check - UTC " + str(hour).zfill(2) + ":" + str(minute).zfill(2))
    n = get_nepse()
    live = get_live_data(n)
    if live is None or live.empty:
        log.warning("No live data - market may be closed")
        return
    sector_map = get_sector_map(n)
    rs_final, week52, vol_med, rs_score, sector_avg = compute_rs(live, sector_map, n)
    if hour == 5 and minute <= 20:
        morning_briefing(live, rs_final, sector_map, rs_score, sector_avg)
    elif hour == 9 and minute >= 25:
        eod_summary(live, sector_map)
    else:
        alerts = check_alerts(live, rs_final, week52, vol_med, sector_map)
        log.info("Done - " + str(alerts) + " alerts sent")

if __name__ == "__main__":
    run()
