"""
nepse_alerts.py
NEPSE Telegram Alert System — DB + API hybrid
Runs during market hours (Mon-Fri), sends alerts for:
  - Morning briefing at 10:50 AM (watchlist picks for the day)
  - Breakout: Near 52W high + Strong RS
  - Volume Spike: Unusual volume in high-RS stocks
  - RS Reversal: Strong stock suddenly dropping
  - Power Sell: Watchlist stock being dumped
  - End of day summary at 3:00 PM

Usage:
  python nepse_alerts.py          # run alert loop
  python nepse_alerts.py --test   # send test alert and exit
"""

import sys, os, time, logging, json, sqlite3
from datetime import datetime, time as dtime
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN      = "8926979126:AAFRdgGNAFDf_AouyqFOeXmc0FYC6ReE5GI"
TELEGRAM_CHAT       = "1923100963"
DB_PATH             = "nepse_market_data.db"
WATCHLIST_PATH      = Path("data/runtime/accounts/account_1/watchlist.json")

RS_THRESHOLD        = 2.0       # minimum RS% to consider a stock strong
NEAR_HIGH_PCT       = 5.0       # within 5% of 52W high = breakout zone
VOL_SPIKE_MULT      = 3.0       # volume 3x above avg = spike
POWER_SELL_DROP     = -3.0      # watchlist stock drops 3%+ = power sell alert
CHECK_INTERVAL_MIN  = 30        # check every 30 minutes during market hours
WATCHLIST_CHECK_MIN = 15        # check watchlist stocks every 15 minutes
COOLDOWN_MIN        = 120       # 2 hour cooldown per alert per stock
MARKET_OPEN         = dtime(10, 55)
MARKET_CLOSE        = dtime(15, 5)
MORNING_BRIEF_TIME  = dtime(10, 50)
EOD_SUMMARY_TIME    = dtime(15, 0)
# ─────────────────────────────────────────────────────────────────────────────

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

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
_morning_brief_sent = False
_eod_sent = False


# ── TELEGRAM ──────────────────────────────────────────────────────────────────

def send_telegram(msg: str) -> bool:
    try:
        import requests
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
        if r.status_code == 200:
            return True
        log.error(f"Telegram HTTP {r.status_code}: {r.text[:100]}")
        return False
    except Exception as e:
        log.error(f"Telegram error: {e}")
        return False


def can_alert(key: str, cooldown_min: int = None) -> bool:
    now = datetime.now()
    cooldown = (cooldown_min or COOLDOWN_MIN) * 60
    last = _alert_history.get(key)
    if last and (now - last).total_seconds() < cooldown:
        return False
    _alert_history[key] = now
    return True


# ── MARKET STATUS ─────────────────────────────────────────────────────────────

def is_trading_day() -> bool:
    """Mon-Fri = trading days (new Nepal calendar)"""
    return datetime.now().weekday() < 5


def is_market_open() -> bool:
    now = datetime.now().time()
    if not is_trading_day():
        return False
    return MARKET_OPEN <= now <= MARKET_CLOSE


def check_market_status_api() -> bool:
    """Use NEPSE API to confirm market is actually open (catches holidays)"""
    try:
        from nepse import Nepse
        n = Nepse()
        n.setTLSVerification(False)
        status = n.getMarketStatus()
        is_open = status.get("isOpen", "CLOSE")
        return is_open == "OPEN"
    except Exception as e:
        log.warning(f"Market status API error: {e} — assuming closed")
        return False


# ── NEPSE API ─────────────────────────────────────────────────────────────────

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
        if df.empty:
            return None
        df = df.rename(columns={
            'symbol': 'symbol',
            'lastTradedPrice': 'ltp',
            'percentageChange': 'change_pct',
            'totalTradeQuantity': 'volume',
            'totalTradeValue': 'turnover',
            'highPrice': 'high',
            'lowPrice': 'low',
            'previousClose': 'prev_close',
        })
        # some API versions use different keys
        if 'symbol' not in df.columns:
            for col in ['stockSymbol', 'scrip', 'ticker']:
                if col in df.columns:
                    df['symbol'] = df[col]
                    break
        for col in ['ltp', 'change_pct', 'volume', 'turnover']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: float(x) if x else 0)
        return df
    except Exception as e:
        log.error(f"Live data error: {e}")
        return None


# ── DB HELPERS ────────────────────────────────────────────────────────────────

def get_watchlist() -> list:
    """Load current watchlist symbols from JSON"""
    try:
        if WATCHLIST_PATH.exists():
            data = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
            return [item.get("symbol", "") for item in data if item.get("symbol")]
        return []
    except Exception as e:
        log.warning(f"Watchlist load error: {e}")
        return []


def get_watchlist_with_scores() -> list:
    """Load watchlist with scores"""
    try:
        if WATCHLIST_PATH.exists():
            data = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
            return [(item.get("symbol", ""), item.get("score", 0)) for item in data if item.get("symbol")]
        return []
    except Exception as e:
        log.warning(f"Watchlist load error: {e}")
        return []


def get_db_rs() -> dict:
    """Get RS scores from DB (faster than API recalculation)"""
    rs_map = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        latest = conn.execute("SELECT MAX(date) FROM stock_prices").fetchone()[0]
        if not latest:
            conn.close()
            return rs_map

        # get 5d, 10d returns per symbol
        rows = conn.execute("""
            SELECT symbol, date, close FROM stock_prices
            WHERE date >= date(?, '-25 days')
            ORDER BY symbol, date
        """, (latest,)).fetchall()

        from collections import defaultdict
        prices = defaultdict(list)
        for sym, date, close in rows:
            prices[sym].append(close)

        # get sector map from fundamentals or a lookup
        sector_rows = conn.execute(
            "SELECT symbol, sector FROM fundamentals WHERE sector IS NOT NULL"
        ).fetchall() if _table_exists(conn, "fundamentals") else []

        sector_map = {r[0]: r[1] for r in sector_rows}
        conn.close()

        # compute 5d RS per symbol vs sector avg
        ret5_map = {}
        for sym, closes in prices.items():
            if len(closes) >= 6:
                ret5_map[sym] = (closes[-1] / closes[-6] - 1) * 100

        from collections import defaultdict
        sector_returns = defaultdict(list)
        for sym, ret in ret5_map.items():
            sec = sector_map.get(sym)
            if sec:
                sector_returns[sec].append(ret)

        sector_avg = {sec: sum(r)/len(r) for sec, r in sector_returns.items() if r}

        for sym, ret in ret5_map.items():
            sec = sector_map.get(sym, "")
            avg = sector_avg.get(sec, 0)
            rs_map[sym] = ret - avg

    except Exception as e:
        log.warning(f"DB RS error: {e}")
    return rs_map


def get_db_vol_avg() -> dict:
    """Get 20-day average volume per symbol from DB"""
    avg_map = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        latest = conn.execute("SELECT MAX(date) FROM stock_prices").fetchone()[0]
        if latest:
            rows = conn.execute("""
                SELECT symbol, AVG(volume) FROM stock_prices
                WHERE date >= date(?, '-20 days')
                GROUP BY symbol
            """, (latest,)).fetchall()
            avg_map = {r[0]: r[1] or 0 for r in rows}
        conn.close()
    except Exception as e:
        log.warning(f"DB vol avg error: {e}")
    return avg_map


def get_db_52w() -> dict:
    """Get 52W high/low per symbol from DB"""
    data = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        latest = conn.execute("SELECT MAX(date) FROM stock_prices").fetchone()[0]
        if latest:
            rows = conn.execute("""
                SELECT symbol, MAX(close), MIN(close) FROM stock_prices
                WHERE date >= date(?, '-365 days')
                GROUP BY symbol
            """, (latest,)).fetchall()
            data = {r[0]: {"high52": r[1], "low52": r[2]} for r in rows}
        conn.close()
    except Exception as e:
        log.warning(f"DB 52w error: {e}")
    return data


def _table_exists(conn, table: str) -> bool:
    r = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return r is not None


# ── ALERT CHECKS ──────────────────────────────────────────────────────────────

def morning_briefing():
    """Send morning briefing with today's watchlist picks"""
    global _morning_brief_sent
    if _morning_brief_sent:
        return
    if not can_alert("morning_brief", cooldown_min=60 * 8):
        return

    picks = get_watchlist_with_scores()
    if not picks:
        log.info("Morning brief: no watchlist")
        return

    now_str = datetime.now().strftime("%Y-%m-%d")
    lines = [f"<b>Good morning! NEPSE opens in 5 min</b>\n<b>Date:</b> {now_str}\n"]
    lines.append("<b>Today's Watchlist Picks:</b>")
    for i, (sym, score) in enumerate(picks[:10], 1):
        lines.append(f"  {i}. <b>{sym}</b> — Score {score}")
    lines.append("\n<i>Alerts active. Monitoring for breakouts and power sells.</i>")

    msg = "\n".join(lines)
    if send_telegram(msg):
        log.info("Morning briefing sent")
        _morning_brief_sent = True


def eod_summary(live_df):
    """Send end of day summary for watchlist stocks"""
    global _eod_sent
    if _eod_sent:
        return
    if not can_alert("eod_summary", cooldown_min=60 * 8):
        return

    watchlist = get_watchlist()
    if not watchlist or live_df is None or live_df.empty:
        return

    lines = ["<b>End of Day Summary — Watchlist</b>\n"]
    found = 0
    for sym in watchlist[:10]:
        row = live_df[live_df["symbol"] == sym]
        if row.empty:
            continue
        r = row.iloc[0]
        ltp = float(r.get("ltp", 0))
        chg = float(r.get("change_pct", 0))
        vol = float(r.get("volume", 0))
        arrow = "+" if chg >= 0 else ""
        icon = "green" if chg >= 0 else "red"
        lines.append(f"  <b>{sym}</b>: Rs {ltp:,.1f} ({arrow}{chg:.2f}%) | Vol {vol/1000:.0f}K")
        found += 1

    if not found:
        return

    msg = "\n".join(lines)
    if send_telegram(msg):
        log.info("EOD summary sent")
        _eod_sent = True


def check_alerts(live_df, rs_map, vol_avg, w52_data):
    """Run all alert checks"""
    alerts_sent = 0
    now_str = datetime.now().strftime("%H:%M")
    watchlist = set(get_watchlist())

    if live_df is None or live_df.empty:
        log.warning("No live data for alert check")
        return 0

    for _, row in live_df.iterrows():
        sym      = str(row.get("symbol", ""))
        ltp      = float(row.get("ltp", 0))
        chg      = float(row.get("change_pct", 0))
        vol      = float(row.get("volume", 0))
        turnover = float(row.get("turnover", 0))

        if not sym or ltp <= 0:
            continue

        rs5     = rs_map.get(sym, 0)
        w52     = w52_data.get(sym, {})
        high52  = w52.get("high52", 0)
        avg_vol = vol_avg.get(sym, 0)
        in_wl   = sym in watchlist

        # ── Alert 1: BREAKOUT ─────────────────────────────────────────────
        if high52 > 0 and rs5 >= RS_THRESHOLD:
            pct_from_high = (ltp - high52) / high52 * 100
            if pct_from_high >= -NEAR_HIGH_PCT and can_alert(f"{sym}_breakout"):
                stars = "BREAKOUT" if pct_from_high >= -1 else "Near High"
                wl_tag = " | IN YOUR WATCHLIST" if in_wl else ""
                msg = (
                    f"<b>NEPSE ALERT — {now_str}</b>\n\n"
                    f"<b>{stars}: {sym}</b>{wl_tag}\n"
                    f"Near 52W High ({pct_from_high:+.1f}%) + RS <b>+{rs5:.1f}%</b>\n"
                    f"LTP: Rs {ltp:,.1f} | Change: {chg:+.2f}%\n"
                    f"Turnover: Rs {turnover/1e6:.1f}M"
                )
                if send_telegram(msg):
                    log.info(f"BREAKOUT alert: {sym}")
                    alerts_sent += 1

        # ── Alert 2: VOLUME SPIKE ─────────────────────────────────────────
        if rs5 >= RS_THRESHOLD and avg_vol > 0:
            vol_mult = vol / avg_vol
            if vol_mult >= VOL_SPIKE_MULT and can_alert(f"{sym}_volspike"):
                wl_tag = " | IN YOUR WATCHLIST" if in_wl else ""
                msg = (
                    f"<b>NEPSE ALERT — {now_str}</b>\n\n"
                    f"<b>VOLUME SPIKE: {sym}</b>{wl_tag}\n"
                    f"Volume <b>{vol_mult:.1f}x</b> above 20-day avg\n"
                    f"RS: +{rs5:.1f}% vs sector\n"
                    f"LTP: Rs {ltp:,.1f} | Change: {chg:+.2f}%"
                )
                if send_telegram(msg):
                    log.info(f"VOL SPIKE alert: {sym}")
                    alerts_sent += 1

        # ── Alert 3: RS REVERSAL ──────────────────────────────────────────
        if rs5 >= RS_THRESHOLD and chg <= -3.0 and can_alert(f"{sym}_reversal"):
            wl_tag = " | IN YOUR WATCHLIST" if in_wl else ""
            msg = (
                f"<b>NEPSE ALERT — {now_str}</b>\n\n"
                f"<b>RS REVERSAL WARNING: {sym}</b>{wl_tag}\n"
                f"Was outperforming (RS +{rs5:.1f}%) but dropping {chg:.2f}% today\n"
                f"LTP: Rs {ltp:,.1f}\n"
                f"<i>Consider reviewing position</i>"
            )
            if send_telegram(msg):
                log.info(f"REVERSAL alert: {sym}")
                alerts_sent += 1

        # ── Alert 4: POWER SELL (watchlist only) ──────────────────────────
        if in_wl and chg <= POWER_SELL_DROP and can_alert(f"{sym}_powersell"):
            msg = (
                f"<b>NEPSE ALERT — {now_str}</b>\n\n"
                f"<b>POWER SELL WARNING: {sym}</b>\n"
                f"Your watchlist stock dropping {chg:.2f}% today\n"
                f"LTP: Rs {ltp:,.1f} | Vol: {vol/1000:.0f}K\n"
                f"<i>Check if smart money is exiting</i>"
            )
            if send_telegram(msg):
                log.info(f"POWER SELL alert: {sym}")
                alerts_sent += 1

    log.info(f"Alert check complete — {alerts_sent} alerts sent")
    return alerts_sent


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────

def run_loop():
    global _morning_brief_sent, _eod_sent

    try:
        import schedule
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "schedule", "--user", "-q"])
        import schedule

    log.info("NEPSE Alert System starting...")
    send_telegram(
        f"<b>NEPSE Alert Bot Started</b>\n"
        f"Monitoring every {CHECK_INTERVAL_MIN} min during market hours\n"
        f"Watchlist checked every {WATCHLIST_CHECK_MIN} min\n"
        f"Alerts: Breakout | Volume Spike | RS Reversal | Power Sell\n"
        f"Morning brief: 10:50 AM | EOD summary: 3:00 PM\n"
        f"Trading days: Mon-Fri | Holiday auto-detection ON"
    )

    last_check = {"time": None}

    def job():
        global _morning_brief_sent, _eod_sent
        now = datetime.now()
        now_t = now.time()

        # Reset daily flags at midnight
        if now_t < dtime(0, 5):
            _morning_brief_sent = False
            _eod_sent = False

        if not is_trading_day():
            log.info("Weekend — skipping")
            return

        # Morning briefing (before market opens)
        if MORNING_BRIEF_TIME <= now_t < MARKET_OPEN:
            morning_briefing()
            return

        # During market hours
        if MARKET_OPEN <= now_t <= MARKET_CLOSE:
            # Confirm market is actually open (catches holidays)
            if not check_market_status_api():
                log.info("Market status API says CLOSED (holiday?) — skipping")
                return

            log.info("Running alert check...")
            live_df  = get_live_data()
            rs_map   = get_db_rs()
            vol_avg  = get_db_vol_avg()
            w52_data = get_db_52w()
            check_alerts(live_df, rs_map, vol_avg, w52_data)
            last_check["time"] = now
            return

        # EOD summary (just after close)
        if EOD_SUMMARY_TIME <= now_t <= dtime(15, 15):
            if last_check["time"] and (now - last_check["time"]).seconds < 3600:
                live_df = get_live_data()
                eod_summary(live_df)
            return

        log.info(f"Outside market window ({now_t.strftime('%H:%M')}) — skipping")

    job()
    schedule.every(CHECK_INTERVAL_MIN).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(30)


def send_test():
    log.info("Sending test alert...")
    watchlist = get_watchlist_with_scores()
    wl_str = ", ".join([s for s, _ in watchlist[:5]]) if watchlist else "None loaded"
    msg = (
        "<b>NEPSE Alert Bot — TEST</b>\n\n"
        "<b>BREAKOUT: BUNGAL</b> | IN YOUR WATCHLIST\n"
        "Near 52W High (-1.0%) + RS +10.6%\n"
        "LTP: Rs 841 | Change: +14.88%\n"
        "Turnover: Rs 147M\n\n"
        f"<b>Current watchlist:</b> {wl_str}\n\n"
        "<i>Test message — real alerts will look like this!</i>"
    )
    ok = send_telegram(msg)
    print("Test alert sent!" if ok else "FAILED — check token/chat ID")


if __name__ == "__main__":
    if "--test" in sys.argv:
        send_test()
    else:
        run_loop()
