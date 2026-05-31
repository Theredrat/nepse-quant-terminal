"""
nepse_alerts.py
NEPSE Telegram Alert System — No database required, API only
Runs during market hours, sends alerts for:
- ★★★ Breakout: Near 52W high + Strong RS
- Volume Spike: Unusual volume in high-RS stocks
- RS Reversal: Strong stock suddenly dropping

Usage:
  python nepse_alerts.py          # run alert loop
  python nepse_alerts.py --test   # send test alert and exit
"""

import sys, time, logging
from datetime import datetime, time as dtime

# ── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN  = "8926979126:AAFRdgGNAFDf_AouyqFOeXmc0FYC6ReE5GI"
TELEGRAM_CHAT   = "1923100963"

RS_THRESHOLD        = 2.0
NEAR_HIGH_PCT       = 5.0
VOL_SPIKE_MULT      = 5.0
CHECK_INTERVAL_MIN  = 30
MARKET_OPEN         = dtime(10, 55)
MARKET_CLOSE        = dtime(15, 5)
COOLDOWN_MIN        = 120
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("nepse_alerts.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)

_alert_history: dict = {}


def send_telegram(msg: str) -> bool:
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


def can_alert(key: str) -> bool:
    now = datetime.now()
    last = _alert_history.get(key)
    if last and (now - last).seconds < COOLDOWN_MIN * 60:
        return False
    _alert_history[key] = now
    return True


def is_market_open() -> bool:
    now = datetime.now().time()
    today = datetime.now().weekday()
    if today >= 5:
        return False
    return MARKET_OPEN <= now <= MARKET_CLOSE


def get_nepse():
    from nepse import Nepse
    n = Nepse()
    n.setTLSVerification(False)
    return n


def get_live_data():
    """Get live market snapshot from NEPSE API"""
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
    """Get symbol -> sector mapping"""
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


def get_price_history(symbol: str, days: int = 40):
    """Get recent price history for a symbol"""
    try:
        import pandas as pd
        n = get_nepse()
        data = n.getCompanyPriceVolumeHistory(symbol)
        if data is None:
            return None
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        if df.empty:
            return None
        # normalize close column
        for col in ['closePrice', 'close', 'lastTradedPrice']:
            if col in df.columns:
                df = df.rename(columns={col: 'close'})
                break
        for col in ['businessDate', 'date', 'transactionDate']:
            if col in df.columns:
                df = df.rename(columns={col: 'date'})
                break
        if 'close' not in df.columns or 'date' not in df.columns:
            return None
        df['close'] = df['close'].apply(lambda x: float(x) if x else 0)
        df = df[df['close'] > 0].sort_values('date').tail(days)
        return df
    except Exception as e:
        log.error(f"History error {symbol}: {e}")
        return None


def calculate_rs_and_52w(live_df, sector_map):
    """
    Calculate RS and 52W high/low using:
    - getLiveMarket for today's prices + today's high/low
    - getCompanyPriceVolumeHistory for 5D returns and volume medians
    Only fetches history for top stocks by turnover to stay within API limits.
    """
    import pandas as pd

    # Filter top 80 stocks by turnover for history fetch (API limit friendly)
    top = live_df.nlargest(80, 'turnover') if 'turnover' in live_df.columns else live_df.head(80)
    symbols = list(top['symbol'].dropna().unique())

    rs_data = {}
    week52_data = {}
    vol_median = {}

    log.info(f"Fetching history for {len(symbols)} top stocks...")

    for sym in symbols:
        try:
            hist = get_price_history(sym, days=365)
            if hist is None or len(hist) < 6:
                continue

            closes = hist['close'].values

            # 52W high/low from history
            week52_data[sym] = {
                'high52': float(hist['close'].max()),
                'low52': float(hist['close'].min()),
                'sector': sector_map.get(sym, '')
            }

            # 5D return for RS
            ret5 = (closes[-1] / closes[-6] - 1) * 100 if len(closes) >= 6 else 0
            rs_data[sym] = {
                'ret5': ret5,
                'sector': sector_map.get(sym, '')
            }

            # Volume median from history
            if 'totalTradeQuantity' in hist.columns:
                vol_median[sym] = float(hist['totalTradeQuantity'].median())
            elif 'volume' in hist.columns:
                vol_median[sym] = float(hist['volume'].median())

            time.sleep(0.15)  # be nice to NEPSE API

        except Exception as e:
            log.warning(f"Skip {sym}: {e}")
            continue

    # Calculate RS = stock 5D return - sector avg 5D return
    import collections
    sector_returns = collections.defaultdict(list)
    for sym, d in rs_data.items():
        if d['sector']:
            sector_returns[d['sector']].append(d['ret5'])

    sector_avg = {sec: sum(rets)/len(rets) for sec, rets in sector_returns.items() if rets}

    rs_score = {}
    for sym, d in rs_data.items():
        sec_avg = sector_avg.get(d['sector'], 0)
        rs_score[sym] = d['ret5'] - sec_avg

    return rs_score, week52_data, vol_median


def check_alerts():
    """Run all alert checks and send Telegram messages"""
    log.info("Running alert check...")

    live = get_live_data()
    if live is None or live.empty:
        log.warning("No live data")
        return 0

    sector_map = get_sector_map()
    rs_score, week52_data, vol_median = calculate_rs_and_52w(live, sector_map)

    alerts_sent = 0
    now_str = datetime.now().strftime("%H:%M")

    for _, row in live.iterrows():
        sym      = str(row.get("symbol", ""))
        ltp      = float(row.get("ltp", 0))
        chg      = float(row.get("change_pct", 0))
        vol      = float(row.get("volume", 0))
        turnover = float(row.get("turnover", 0))

        if not sym or ltp <= 0:
            continue

        rs5    = rs_score.get(sym, 0)
        w52    = week52_data.get(sym, {})
        high52 = w52.get("high52", 0)
        sector = w52.get("sector", sector_map.get(sym, ""))
        med_vol = vol_median.get(sym, 0)

        # ── Alert 1: BREAKOUT ─────────────────────────────────────────────────
        if high52 > 0 and rs5 >= RS_THRESHOLD:
            pct_from_high = (ltp - high52) / high52 * 100
            if pct_from_high >= -NEAR_HIGH_PCT and can_alert(f"{sym}_breakout"):
                stars = "★★★" if pct_from_high >= -1 else "★★"
                msg = (
                    f"🚨 <b>NEPSE ALERT — {now_str}</b>\n\n"
                    f"{stars} <b>BREAKOUT: {sym}</b>\n"
                    f"Near 52W High ({pct_from_high:+.1f}%) + RS <b>+{rs5:.1f}%</b>\n"
                    f"LTP: Rs {ltp:,.1f} | Change: {chg:+.2f}%\n"
                    f"Turnover: Rs {turnover/1e6:.1f}M\n"
                    f"Sector: {sector}"
                )
                if send_telegram(msg):
                    log.info(f"BREAKOUT alert: {sym}")
                    alerts_sent += 1

        # ── Alert 2: VOLUME SPIKE ─────────────────────────────────────────────
        if rs5 >= RS_THRESHOLD and med_vol > 0:
            vol_mult = vol / med_vol
            if vol_mult >= VOL_SPIKE_MULT and can_alert(f"{sym}_volspike"):
                msg = (
                    f"📈 <b>NEPSE ALERT — {now_str}</b>\n\n"
                    f"⚡ <b>VOLUME SPIKE: {sym}</b>\n"
                    f"Volume <b>{vol_mult:.1f}x</b> above average\n"
                    f"RS: +{rs5:.1f}% vs sector\n"
                    f"LTP: Rs {ltp:,.1f} | Change: {chg:+.2f}%\n"
                    f"Sector: {sector}"
                )
                if send_telegram(msg):
                    log.info(f"VOL SPIKE alert: {sym}")
                    alerts_sent += 1

        # ── Alert 3: RS REVERSAL ──────────────────────────────────────────────
        if rs5 >= RS_THRESHOLD and chg <= -3.0 and can_alert(f"{sym}_reversal"):
            msg = (
                f"⚠️ <b>NEPSE ALERT — {now_str}</b>\n\n"
                f"🔻 <b>RS REVERSAL WARNING: {sym}</b>\n"
                f"Was outperforming (RS +{rs5:.1f}%) but dropping {chg:.2f}% today\n"
                f"LTP: Rs {ltp:,.1f}\n"
                f"Sector: {sector}\n"
                f"<i>Consider reviewing position</i>"
            )
            if send_telegram(msg):
                log.info(f"REVERSAL alert: {sym}")
                alerts_sent += 1

    log.info(f"Alert check complete — {alerts_sent} alerts sent")
    return alerts_sent


def run_loop():
    """Main alert loop"""
    try:
        import schedule
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "schedule", "--user", "-q"])
        import schedule

    log.info("NEPSE Alert System started (API-only mode)")
    send_telegram(
        f"✅ <b>NEPSE Alert Bot Started</b>\n"
        f"Monitoring every {CHECK_INTERVAL_MIN} min\n"
        f"Market hours: {MARKET_OPEN.strftime('%H:%M')} - {MARKET_CLOSE.strftime('%H:%M')}\n"
        f"Alerts: Breakout | Volume Spike | RS Reversal\n"
        f"<i>API-only mode — no database needed</i>"
    )

    def job():
        if is_market_open():
            check_alerts()
        else:
            log.info("Market closed — skipping check")

    job()
    schedule.every(CHECK_INTERVAL_MIN).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(30)


def send_test():
    log.info("Sending test alert...")
    msg = (
        "🧪 <b>NEPSE Alert Bot — TEST</b>\n\n"
        "★★★ <b>BREAKOUT: BUNGAL</b>\n"
        "Near 52W High (-1.0%) + RS +10.6%\n"
        "LTP: Rs 732 | Change: +0.27%\n"
        "Turnover: Rs 43M\n"
        "Sector: Hydro Power\n\n"
        "<i>This is a test message. Real alerts will look like this!</i>"
    )
    ok = send_telegram(msg)
    print("Test alert sent!" if ok else "Failed to send — check token/chat ID")


if __name__ == "__main__":
    if "--test" in sys.argv:
        send_test()
    else:
        run_loop()
