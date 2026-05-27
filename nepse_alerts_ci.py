"""
nepse_alerts_ci.py
Single-pass version for GitHub Actions - runs once and exits
Reads credentials from environment variables
"""
import os, sys, time, logging
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8926979126:AAFRdgGNAFDf_AouyqFOeXmc0FYC6ReE5GI")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT",  "1923100963")

RS_THRESHOLD   = 2.0
NEAR_HIGH_PCT  = 5.0
VOL_SPIKE_MULT = 5.0
COOLDOWN_MIN   = 60

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

_alert_history = {}

def send_telegram(msg):
    try:
        import requests
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        log.error(f"Telegram error: {e}")
        return False

def can_alert(key):
    now = datetime.now()
    last = _alert_history.get(key)
    if last and (now - last).seconds < COOLDOWN_MIN * 60:
        return False
    _alert_history[key] = now
    return True

def get_nepse():
    from nepse import Nepse
    n = Nepse()
    n.setTLSVerification(False)
    return n

def get_live_data():
    try:
        import pandas as pd
        n = get_nepse()
        data = n.getLiveMarket()
        if data is None:
            return None
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        df = df.rename(columns={
            'lastTradedPrice': 'ltp',
            'percentageChange': 'change_pct',
            'totalTradeQuantity': 'volume',
            'totalTradeValue': 'turnover',
            'highPrice': 'high',
            'lowPrice': 'low',
            'previousClose': 'prev_close',
        })
        for col in ['ltp', 'change_pct', 'volume', 'turnover', 'high', 'low']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: float(x) if x else 0)
        return df
    except Exception as e:
        log.error(f"Live data error: {e}")
        return None

def get_sector_map():
    try:
        import pandas as pd
        n = get_nepse()
        data = n.getCompanyList()
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        if 'symbol' in df.columns and 'sectorName' in df.columns:
            return dict(zip(df['symbol'], df['sectorName']))
        return {}
    except Exception as e:
        log.error(f"Sector map error: {e}")
        return {}

def get_price_history(sym, days=40):
    try:
        import pandas as pd
        n = get_nepse()
        data = n.getCompanyPriceVolumeHistory(sym)
        if data is None:
            return None
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        if df.empty:
            return None
        for col in ['closePrice', 'close', 'lastTradedPrice']:
            if col in df.columns:
                df = df.rename(columns={col: 'close'}); break
        for col in ['businessDate', 'date', 'transactionDate']:
            if col in df.columns:
                df = df.rename(columns={col: 'date'}); break
        if 'close' not in df.columns:
            return None
        df['close'] = df['close'].apply(lambda x: float(x) if x else 0)
        return df[df['close'] > 0].sort_values('date').tail(days)
    except Exception as e:
        log.warning(f"History error {sym}: {e}")
        return None

def run():
    log.info("GitHub Actions alert check starting...")
    live = get_live_data()
    if live is None or live.empty:
        log.warning("No live data - market may be closed")
        return

    sector_map = get_sector_map()
    top = live.nlargest(80, 'turnover') if 'turnover' in live.columns else live.head(80)
    symbols = list(top['symbol'].dropna().unique())

    rs_score = {}
    week52_data = {}
    vol_median = {}
    import collections
    ret5_by_sector = collections.defaultdict(list)

    log.info(f"Fetching history for {len(symbols)} stocks...")
    for sym in symbols:
        try:
            hist = get_price_history(sym, days=365)
            if hist is None or len(hist) < 6:
                continue
            closes = hist['close'].values
            week52_data[sym] = {'high52': float(hist['close'].max()), 'low52': float(hist['close'].min()), 'sector': sector_map.get(sym,'')}
            ret5 = (closes[-1] / closes[-6] - 1) * 100 if len(closes) >= 6 else 0
            rs_score[sym] = {'ret5': ret5, 'sector': sector_map.get(sym,'')}
            if 'totalTradeQuantity' in hist.columns:
                vol_median[sym] = float(hist['totalTradeQuantity'].median())
            elif 'volume' in hist.columns:
                vol_median[sym] = float(hist['volume'].median())
            ret5_by_sector[sector_map.get(sym,'')].append(ret5)
            time.sleep(0.15)
        except Exception as e:
            log.warning(f"Skip {sym}: {e}")

    sector_avg = {s: sum(v)/len(v) for s, v in ret5_by_sector.items() if v}
    rs_final = {sym: d['ret5'] - sector_avg.get(d['sector'], 0) for sym, d in rs_score.items()}

    alerts_sent = 0
    now_str = datetime.now().strftime("%H:%M")

    for _, row in live.iterrows():
        sym = str(row.get("symbol", ""))
        ltp = float(row.get("ltp", 0))
        chg = float(row.get("change_pct", 0))
        vol = float(row.get("volume", 0))
        turnover = float(row.get("turnover", 0))
        if not sym or ltp <= 0:
            continue

        rs5    = rs_final.get(sym, 0)
        w52    = week52_data.get(sym, {})
        high52 = w52.get("high52", 0)
        sector = w52.get("sector", sector_map.get(sym, ""))
        med_vol = vol_median.get(sym, 0)

        # Breakout
        if high52 > 0 and rs5 >= RS_THRESHOLD:
            pct_from_high = (ltp - high52) / high52 * 100
            if pct_from_high >= -NEAR_HIGH_PCT and can_alert(f"{sym}_breakout"):
                stars = "★★★" if pct_from_high >= -1 else "★★"
                send_telegram(
                    f"🚨 <b>NEPSE ALERT — {now_str}</b>\n\n"
                    f"{stars} <b>BREAKOUT: {sym}</b>\n"
                    f"Near 52W High ({pct_from_high:+.1f}%) + RS <b>+{rs5:.1f}%</b>\n"
                    f"LTP: Rs {ltp:,.1f} | Change: {chg:+.2f}%\n"
                    f"Turnover: Rs {turnover/1e6:.1f}M | Sector: {sector}"
                )
                log.info(f"BREAKOUT: {sym}")
                alerts_sent += 1

        # Volume spike
        if rs5 >= RS_THRESHOLD and med_vol > 0:
            vol_mult = vol / med_vol
            if vol_mult >= VOL_SPIKE_MULT and can_alert(f"{sym}_volspike"):
                send_telegram(
                    f"📈 <b>NEPSE ALERT — {now_str}</b>\n\n"
                    f"⚡ <b>VOLUME SPIKE: {sym}</b>\n"
                    f"Volume <b>{vol_mult:.1f}x</b> above average\n"
                    f"RS: +{rs5:.1f}% | LTP: Rs {ltp:,.1f} | Change: {chg:+.2f}%\n"
                    f"Sector: {sector}"
                )
                log.info(f"VOL SPIKE: {sym}")
                alerts_sent += 1

        # RS Reversal
        if rs5 >= RS_THRESHOLD and chg <= -3.0 and can_alert(f"{sym}_reversal"):
            send_telegram(
                f"⚠️ <b>NEPSE ALERT — {now_str}</b>\n\n"
                f"🔻 <b>RS REVERSAL: {sym}</b>\n"
                f"Was outperforming (RS +{rs5:.1f}%) but dropping {chg:.2f}% today\n"
                f"LTP: Rs {ltp:,.1f} | Sector: {sector}"
            )
            log.info(f"REVERSAL: {sym}")
            alerts_sent += 1

    log.info(f"Done — {alerts_sent} alerts sent")

if __name__ == "__main__":
    run()
