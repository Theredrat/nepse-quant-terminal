# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from colorama import Fore, Back, Style, init
import warnings
warnings.filterwarnings("ignore")

init(autoreset=True)

DB_PATH = "nepse_market_data.db"

# -----------------------------------------------------------
#  DATABASE
# -----------------------------------------------------------


def mentor_broker_comment(verdict, n_buyers, n_sellers, top_buyer_pct, top_seller_pct):
    total = n_buyers + n_sellers
    buyer_pct = round(n_buyers / total * 100) if total > 0 else 0
    print("")
    print("  -------------------------------------------------------")
    print("  MENTOR SAYS:")
    
    if verdict == "STRONG ACCUMULATION":
        if top_buyer_pct < 20:
            print("  This is GENUINE BROAD ACCUMULATION.")
            print(f"  {n_buyers} different brokers are net buyers vs {n_sellers} sellers.")
            print(f"  No single broker dominates ({top_buyer_pct:.1f}% concentration).")
            print("  This is real demand - not operator manipulation.")
            print("  MEANING: Smart money is quietly building positions.")
            print("  ACTION: Watch for entry opportunity. Bias is BULLISH.")
        else:
            print("  CONCENTRATED ACCUMULATION detected.")
            print(f"  Buying dominated by few brokers ({top_buyer_pct:.1f}% concentration).")
            print("  Could be operator accumulation phase.")
            print("  MEANING: Someone big is buying. Could be early markup soon.")
            print("  ACTION: Watch closely. Buy only near strong support.")

    elif verdict == "MILD ACCUMULATION":
        print("  Mild buying interest visible.")
        print(f"  More buyers ({n_buyers}) than sellers ({n_sellers}) but not decisive.")
        print("  MEANING: Early signs of interest but not confirmed yet.")
        print("  ACTION: Watch and wait. Do not buy yet.")

    elif verdict == "NEUTRAL":
        print("  Broker activity is balanced.")
        print(f"  {n_buyers} buyers vs {n_sellers} sellers - no clear direction.")
        print("  MEANING: No smart money conviction either way.")
        print("  ACTION: Avoid this stock until clearer signal appears.")

    elif verdict == "MILD DISTRIBUTION":
        print("  Early selling pressure appearing.")
        print(f"  More sellers ({n_sellers}) than buyers ({n_buyers}).")
        print("  MEANING: Smart money may be starting to exit.")
        print("  ACTION: If you hold this - tighten your stop loss.")

    elif verdict == "STRONG DISTRIBUTION":
        if top_seller_pct > 50:
            print("  DANGER: CONCENTRATED DISTRIBUTION detected.")
            print(f"  One broker is dumping ({top_seller_pct:.1f}% of all selling).")
            print("  MEANING: Operator is exiting. Retail is holding the bag.")
            print("  ACTION: EXIT IMMEDIATELY if you hold this stock.")
        else:
            print("  BROAD DISTRIBUTION - many brokers selling.")
            print(f"  {n_sellers} brokers are net sellers vs {n_buyers} buyers.")
            print("  MEANING: Wide selling pressure. No support from smart money.")
            print("  ACTION: Avoid. Exit any existing position.")
    print("  -------------------------------------------------------")

def check_data_freshness():
    from datetime import datetime, timedelta
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT MAX(date) FROM stock_prices")
    latest = cur.fetchone()[0]
    cur.execute("SELECT MAX(date) FROM broker_activity")
    latest_broker = cur.fetchone()[0]
    conn.close()
    
    if not latest:
        return
    
    latest_date = datetime.strptime(latest, "%Y-%m-%d")
    broker_date = datetime.strptime(latest_broker, "%Y-%m-%d")
    today = datetime.now()
    price_age = (today - latest_date).days
    broker_age = (today - broker_date).days
    
    if price_age > 3 or broker_age > 3:
        print(f"")
        print(f"  -------------------------------------------------------")
        print(f"  DATA FRESHNESS WARNING:")
        if price_age > 3:
            print(f"  Price data is {price_age} days old ({latest})")
            print(f"  Check if your scraper is running correctly")
        if broker_age > 3:
            print(f"  Broker data is {broker_age} days old ({latest_broker})")
            print(f"  Analysis may not reflect current market conditions")
        print(f"  -------------------------------------------------------")
    else:
        print(f"  Data: Prices {latest} | Broker {latest_broker} | Fresh OK")

def is_data_quality_ok(df):
    """Returns True if stock data is clean enough to analyse"""
    if len(df) < 60:
        return False, "Insufficient history"
    
    # Check for negative prices
    if (df["close"] <= 0).any():
        return False, "Negative/zero prices found"
    
    # Check last 30 days have reasonable data
    recent = df.tail(30)
    zero_vol_pct = (recent["volume"] <= 0).sum() / len(recent)
    if zero_vol_pct > 0.5:
        return False, "More than 50% zero volume days recently"
    
    # Check price is not suspiciously flat
    recent_std = recent["close"].std()
    if recent_std == 0:
        return False, "Price completely flat - possibly suspended"
    
    return True, "OK"

def get_conn():
    return sqlite3.connect(DB_PATH)

def get_prices(symbol, days=300):
    conn = get_conn()
    df = pd.read_sql_query(f"""
        SELECT date, open, high, low, close, volume
        FROM stock_prices
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT {days}
    """, conn, params=(symbol,))
    conn.close()
    df = df.sort_values("date").reset_index(drop=True)
    return df

def get_all_symbols():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT s.symbol, c.sector
        FROM stock_prices s
        LEFT JOIN companies c ON s.symbol = c.symbol
        WHERE s.date >= date('now', '-30 days')
        AND s.symbol NOT IN (SELECT symbol FROM non_equity_securities)
        AND s.symbol NOT LIKE '%LD%'
        AND s.symbol NOT LIKE '%BLD%'
        AND s.symbol NOT LIKE '%DB%'
        AND s.symbol NOT LIKE '%MF%'
        AND s.symbol NOT LIKE 'SAND%'
        AND s.symbol != 'NEPSE'
            """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_index(days=300):
    conn = get_conn()
    df = pd.read_sql_query(f"""
        SELECT date, open, high, low, close, volume
        FROM benchmark_index_history
        WHERE benchmark = 'NEPSE_PROXY'
        ORDER BY date DESC
        LIMIT {days}
    """, conn)
    conn.close()
    df = df.sort_values("date").reset_index(drop=True)
    return df

def get_broker_data(symbol, days=10):
    conn = get_conn()
    df = pd.read_sql_query(f"""
        SELECT date, broker_id, broker_name, buy_qty, sell_qty, net_qty, buy_val, sell_val, net_val
        FROM broker_activity
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT {days * 20}
    """, conn, params=(symbol,))
    conn.close()
    return df

def get_fundamentals(symbol):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT pe_ratio, pb_ratio, eps, roe, dividend_yield, sector
        FROM fundamentals
        WHERE symbol = ?
        ORDER BY date DESC LIMIT 1
    """, (symbol,))
    row = cur.fetchone()
    conn.close()
    return row

def get_sector_avg(sector):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(pe_ratio), AVG(pb_ratio), AVG(roe)
        FROM fundamentals f
        JOIN companies c ON f.symbol = c.symbol
        WHERE c.sector = ?
        AND f.date >= date('now', '-90 days')
    """, (sector,))
    row = cur.fetchone()
    conn.close()
    return row

def get_unlock_dates(symbol):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT unlock_date FROM unlock_dates
        WHERE symbol = ?
        AND unlock_date >= date('now')
        AND unlock_date <= date('now', '+60 days')
    """, (symbol,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_portfolio():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT symbol, quantity, avg_entry_price, hard_stop_pct, take_profit_pct, strategy_tag
        FROM portfolio_positions
        WHERE status = 'open'
    """, conn)
    conn.close()
    return df

# -----------------------------------------------------------
#  TECHNICAL INDICATORS
# -----------------------------------------------------------

def calc_ma(series, period):
    return series.rolling(window=period).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast).mean()
    ema_slow = series.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calc_atr(df, period=14):
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def detect_support_resistance(df, lookback=50):
    recent = df.tail(lookback)
    highs = []
    lows = []
    for i in range(2, len(recent) - 2):
        if recent["high"].iloc[i] >= recent["high"].iloc[i-1] and \
           recent["high"].iloc[i] >= recent["high"].iloc[i+1] and \
           recent["high"].iloc[i] >= recent["high"].iloc[i-2] and \
           recent["high"].iloc[i] >= recent["high"].iloc[i+2]:
            highs.append(recent["high"].iloc[i])
        if recent["low"].iloc[i] <= recent["low"].iloc[i-1] and \
           recent["low"].iloc[i] <= recent["low"].iloc[i+1] and \
           recent["low"].iloc[i] <= recent["low"].iloc[i-2] and \
           recent["low"].iloc[i] <= recent["low"].iloc[i+2]:
            lows.append(recent["low"].iloc[i])
    support = round(sorted(lows)[-2], 2) if len(lows) >= 2 else round(df["low"].tail(20).min(), 2)
    resistance = round(sorted(highs)[-2], 2) if len(highs) >= 2 else round(df["high"].tail(20).max(), 2)
    return support, resistance

def detect_candlestick(df):
    if len(df) < 3:
        return "INSUFFICIENT DATA"
    c = df.iloc[-1]
    p = df.iloc[-2]
    body = abs(c["close"] - c["open"])
    wick_lower = min(c["open"], c["close"]) - c["low"]
    wick_upper = c["high"] - max(c["open"], c["close"])
    total_range = c["high"] - c["low"]
    if total_range == 0:
        return "DOJI"
    # Hammer
    if wick_lower > 2 * body and wick_upper < body and c["close"] > c["open"]:
        return "HAMMER (Bullish)"
    # Shooting star
    if wick_upper > 2 * body and wick_lower < body and c["close"] < c["open"]:
        return "SHOOTING STAR (Bearish)"
    # Bullish engulfing
    if (c["close"] > c["open"] and p["close"] < p["open"] and
        c["close"] > p["open"] and c["open"] < p["close"]):
        return "BULLISH ENGULFING"
    # Bearish engulfing
    if (c["close"] < c["open"] and p["close"] > p["open"] and
        c["open"] > p["close"] and c["close"] < p["open"]):
        return "BEARISH ENGULFING"
    # Doji
    if body < total_range * 0.1:
        return "DOJI (Indecision)"
    # Strong bullish
    if c["close"] > c["open"] and body > total_range * 0.6:
        return "STRONG BULLISH CANDLE"
    # Strong bearish
    if c["close"] < c["open"] and body > total_range * 0.6:
        return "STRONG BEARISH CANDLE"
    return "NEUTRAL"

def detect_rsi_divergence(df, rsi_series):
    if len(df) < 20:
        return "NONE"
    prices = df["close"].tail(20).values
    rsi = rsi_series.tail(20).values
    # Bearish divergence: price higher high, RSI lower high
    if prices[-1] > prices[-10] and rsi[-1] < rsi[-10]:
        return "BEARISH DIVERGENCE"
    # Bullish divergence: price lower low, RSI higher low
    if prices[-1] < prices[-10] and rsi[-1] > rsi[-10]:
        return "BULLISH DIVERGENCE"
    return "NONE"

# -----------------------------------------------------------
#  MODULE 1 — MARKET REGIME
# -----------------------------------------------------------

def analyze_market_regime():
    print(f"\n{Fore.CYAN}{'-'*55}")
    print(f"  MODULE 1 — MARKET REGIME DETECTOR")
    print(f"{'-'*55}{Style.RESET_ALL}")

    df = get_index(300)
    if df.empty:
        print(f"{Fore.RED}  No index data found.{Style.RESET_ALL}")
        return

    df["ma20"] = calc_ma(df["close"], 20)
    df["ma50"] = calc_ma(df["close"], 50)
    df["ma200"] = calc_ma(df["close"], 200)
    df["rsi"] = calc_rsi(df["close"])
    _, _, df["macd_hist"] = calc_macd(df["close"])
    df["vol_avg20"] = df["volume"].rolling(20).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    price = latest["close"]
    ma20 = latest["ma20"]
    ma50 = latest["ma50"]
    ma200 = latest["ma200"]
    rsi = latest["rsi"]
    macd_hist = latest["macd_hist"]
    vol_ratio = latest["volume"] / latest["vol_avg20"] if latest["vol_avg20"] > 0 else 1

    # Regime scoring
    score = 0
    if price > ma200: score += 2
    if price > ma50: score += 1
    if price > ma20: score += 1
    if ma50 > ma200: score += 2  # Golden cross territory
    if rsi > 50: score += 1
    if macd_hist > 0: score += 1
    if vol_ratio > 1.2: score += 1

    if score >= 7:
        regime = "MARKUP"
        color = Fore.GREEN
        bias = "AGGRESSIVE — Full position sizing"
    elif score >= 5:
        regime = "ACCUMULATION / EARLY MARKUP"
        color = Fore.YELLOW
        bias = "SELECTIVE — Build positions carefully"
    elif score >= 3:
        regime = "DISTRIBUTION / LATE MARKUP"
        color = Fore.YELLOW
        bias = "CAUTIOUS — Reduce exposure, protect profits"
    else:
        regime = "MARKDOWN"
        color = Fore.RED
        bias = "DEFENSIVE — Cash is king, avoid longs"

    pct_vs_200 = ((price - ma200) / ma200 * 100) if ma200 else 0
    ma_cross = "GOLDEN CROSS ?" if ma50 > ma200 else "DEATH CROSS ?"

    print(f"\n  NEPSE Index:     {Fore.WHITE}{price:,.2f}{Style.RESET_ALL}")
    print(f"  vs 200 MA:       {color}{pct_vs_200:+.1f}%{Style.RESET_ALL}")
    print(f"  MA Cross:        {Fore.GREEN if ma50 > ma200 else Fore.RED}{ma_cross}{Style.RESET_ALL}")
    print(f"  RSI:             {Fore.WHITE}{rsi:.1f}{Style.RESET_ALL}")
    print(f"  MACD Histogram:  {Fore.GREEN if macd_hist > 0 else Fore.RED}{'? Positive' if macd_hist > 0 else '? Negative'}{Style.RESET_ALL}")
    print(f"  Volume vs Avg:   {Fore.WHITE}{vol_ratio:.1f}x{Style.RESET_ALL}")
    print(f"\n  {Fore.WHITE}Market Phase:    {color}{regime}{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}Posture:         {Fore.CYAN}{bias}{Style.RESET_ALL}")

    return regime

# -----------------------------------------------------------
#  MODULE 2 — BROKER INTELLIGENCE
# -----------------------------------------------------------

def analyze_broker(symbol):
    df = get_broker_data(symbol)
    if df.empty:
        return {"verdict": "NO DATA", "score": 0, "flags": []}

    flags = []

    # Net position by broker
    broker_net = df.groupby("broker_id").agg(
        total_buy=("buy_qty", "sum"),
        total_sell=("sell_qty", "sum"),
        total_net=("net_qty", "sum"),
        broker_name=("broker_name", "first")
    ).reset_index()

    net_buyers = broker_net[broker_net["total_net"] > 0]
    net_sellers = broker_net[broker_net["total_net"] < 0]
    n_buyers = len(net_buyers)
    n_sellers = len(net_sellers)
    total_brokers = len(broker_net)

    # Concentration check
    top_buyer_pct = 0
    top_seller_pct = 0
    total_buy = broker_net["total_buy"].sum()
    total_sell = broker_net["total_sell"].sum()

    if total_buy > 0 and len(net_buyers) > 0:
        top_buyer_pct = net_buyers["total_buy"].max() / total_buy * 100
    if total_sell > 0 and len(net_sellers) > 0:
        top_seller_pct = net_sellers["total_sell"].max() / total_sell * 100

    # Recent shift — last 3 days vs earlier
    recent_dates = sorted(df["date"].unique())
    if len(recent_dates) >= 2:
        recent = df[df["date"] == recent_dates[-1]]
        recent_net = recent["net_qty"].sum()
        if recent_net < 0:
            flags.append("? Recent day net SELLING")

    # Concentration flag
    if top_seller_pct > 60:
        flags.append("? CONCENTRATED SELLING — 1 broker dominates sell side")

    # Broad accumulation
    broad_accum = n_buyers > n_sellers and n_buyers >= 3

    # Score
    score = 0
    if n_buyers > n_sellers: score += 3
    if broad_accum: score += 2
    if top_seller_pct < 40: score += 1
    if top_buyer_pct < 50: score += 1  # buying is spread out
    score -= len(flags)

    if score >= 5:
        verdict = "STRONG ACCUMULATION"
    elif score >= 3:
        verdict = "MILD ACCUMULATION"
    elif score >= 1:
        verdict = "NEUTRAL"
    elif score >= -1:
        verdict = "MILD DISTRIBUTION"
    else:
        verdict = "STRONG DISTRIBUTION"

    return {
        "verdict": verdict,
        "score": score,
        "n_buyers": n_buyers,
        "n_sellers": n_sellers,
        "top_buyer_pct": top_buyer_pct,
        "top_seller_pct": top_seller_pct,
        "flags": flags
    }

# -----------------------------------------------------------
#  MODULE 3 — FUNDAMENTAL FILTER
# -----------------------------------------------------------

def analyze_fundamentals(symbol):
    row = get_fundamentals(symbol)
    if not row:
        return {"score": 0, "verdict": "NO DATA", "details": {}}

    pe, pb, eps, roe, div_yield, sector = row
    score = 0
    details = {}

    # EPS
    if eps and eps > 0:
        score += 2
        details["EPS"] = f"Rs.{eps:.2f} ?"
    elif eps and eps < 0:
        score -= 2
        details["EPS"] = f"Rs.{eps:.2f} ? (Negative)"
    else:
        details["EPS"] = "N/A"

    # PE vs sector
    if sector and pe:
        sec_avg = get_sector_avg(sector)
        if sec_avg and sec_avg[0]:
            sec_pe = sec_avg[0]
            if pe < sec_pe * 0.8:
                score += 2
                details["PE"] = f"{pe:.1f}x (Sector avg: {sec_pe:.1f}x) Undervalued"
            elif pe < sec_pe * 1.5:
                score += 1
                details["PE"] = f"{pe:.1f}x (Sector avg: {sec_pe:.1f}x) In-line"
            else:
                details["PE"] = f"{pe:.1f}x (Sector avg: {sec_pe:.1f}x) Premium"
        else:
            details["PE"] = f"{pe:.1f}x"

    # PBV
    if pb:
        if pb < 1.5:
            score += 2
            details["PBV"] = f"{pb:.2f}x ?"
        elif pb < 2.5:
            score += 1
            details["PBV"] = f"{pb:.2f}x — Moderate"
        else:
            details["PBV"] = f"{pb:.2f}x ? High"

    # ROE
    if roe:
        if roe > 15:
            score += 2
            details["ROE"] = f"{roe:.1f}% ?"
        elif roe > 10:
            score += 1
            details["ROE"] = f"{roe:.1f}% — Acceptable"
        else:
            details["ROE"] = f"{roe:.1f}% ? Weak"

    # Dividend
    if div_yield and div_yield > 3:
        score += 1
        details["Dividend Yield"] = f"{div_yield:.1f}% ?"

    if score >= 6:
        verdict = "STRONG FUNDAMENTALS"
    elif score >= 3:
        verdict = "DECENT FUNDAMENTALS"
    elif score >= 1:
        verdict = "WEAK FUNDAMENTALS"
    else:
        verdict = "POOR FUNDAMENTALS"

    return {"score": score, "verdict": verdict, "details": details}

# -----------------------------------------------------------
#  MODULE 4 — FULL STOCK ANALYSIS
# -----------------------------------------------------------

def analyze_stock(symbol):
    print(f"\n{Fore.CYAN}{'-'*55}")
    print(f"  FULL ANALYSIS — {symbol}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'-'*55}{Style.RESET_ALL}")

    df = get_prices(symbol, 300)
    if len(df) < 50:
        print(f"{Fore.RED}  Insufficient price data for {symbol}{Style.RESET_ALL}")
        return

    # Indicators
    df["ma20"] = calc_ma(df["close"], 20)
    df["ma50"] = calc_ma(df["close"], 50)
    df["ma200"] = calc_ma(df["close"], 200)
    df["rsi"] = calc_rsi(df["close"])
    df["macd"], df["signal"], df["hist"] = calc_macd(df["close"])
    df["atr"] = calc_atr(df)
    df["vol_avg20"] = df["volume"].rolling(20).mean()

    latest = df.iloc[-1]
    price = latest["close"]
    ma20 = latest["ma20"]
    ma50 = latest["ma50"]
    ma200 = latest["ma200"]
    rsi = latest["rsi"]
    hist = latest["hist"]
    atr = latest["atr"]
    vol_ratio = latest["volume"] / latest["vol_avg20"] if latest["vol_avg20"] > 0 else 1

    support, resistance = detect_support_resistance(df)
    candle = detect_candlestick(df)
    divergence = detect_rsi_divergence(df, df["rsi"])

    # Technical score
    tech_score = 0
    tech_flags = []

    if price > ma200:
        tech_score += 2
        tech_flags.append(("?", "Above 200 MA (Uptrend)"))
    else:
        tech_flags.append(("?", "Below 200 MA (Downtrend)"))

    if price > ma50:
        tech_score += 1
        tech_flags.append(("?", "Above 50 MA"))
    else:
        tech_flags.append(("?", "Below 50 MA"))

    if 40 <= rsi <= 60:
        tech_score += 2
        tech_flags.append(("?", f"RSI {rsi:.1f} — Neutral zone (good entry)"))
    elif rsi < 40:
        tech_score += 1
        tech_flags.append(("?", f"RSI {rsi:.1f} — Oversold (potential bounce)"))
    elif rsi > 70:
        tech_flags.append(("?", f"RSI {rsi:.1f} — Overbought"))

    if hist > 0:
        tech_score += 1
        tech_flags.append(("?", "MACD histogram positive"))
    else:
        tech_flags.append(("?", "MACD histogram negative"))

    if vol_ratio > 1.5:
        tech_score += 1
        tech_flags.append(("?", f"Volume {vol_ratio:.1f}x above average"))

    if "Bullish" in candle or "HAMMER" in candle or "ENGULFING" in candle:
        tech_score += 1
        tech_flags.append(("?", f"Pattern: {candle}"))
    elif "Bearish" in candle or "SHOOTING" in candle:
        tech_flags.append(("?", f"Pattern: {candle}"))
    else:
        tech_flags.append(("—", f"Pattern: {candle}"))

    if divergence == "BULLISH DIVERGENCE":
        tech_score += 2
        tech_flags.append(("?", "RSI Bullish Divergence detected"))
    elif divergence == "BEARISH DIVERGENCE":
        tech_score -= 1
        tech_flags.append(("?", "RSI Bearish Divergence detected"))

    # Broker analysis
    broker = analyze_broker(symbol)

    # Fundamental analysis
    fund = analyze_fundamentals(symbol)

    # Unlock date check
    unlocks = get_unlock_dates(symbol)
    unlock_flag = len(unlocks) > 0

    # Total conviction score (out of 10)
    raw_score = tech_score + broker["score"] + (fund["score"] // 2)
    conviction = min(10, max(0, round(raw_score * 10 / 18)))

    # Trade plan
    stop_loss = round(support * 0.97, 2)
    target1 = round(resistance, 2)
    target2 = round(resistance * 1.08, 2)
    entry_price = price
    risk = entry_price - stop_loss
    reward = target1 - entry_price
    rr = round(reward / risk, 2) if risk > 0 else 0
    near_resistance = (resistance - price) < (price * 0.03)

    # Print results
    print(f"\n  {Fore.WHITE}-- PRICE ACTION --{Style.RESET_ALL}")
    print(f"  Current Price:   Rs. {price:,.2f}")
    print(f"  Support Zone:    Rs. {support:,.2f}")
    print(f"  Resistance:      Rs. {resistance:,.2f}")
    print(f"  ATR (14):        Rs. {atr:,.2f}")

    print(f"\n  {Fore.WHITE}-- TECHNICAL ANALYSIS --{Style.RESET_ALL}")
    for icon, msg in tech_flags:
        color = Fore.GREEN if icon == "?" else (Fore.YELLOW if icon == "?" else Fore.WHITE)
        print(f"  {color}{icon} {msg}{Style.RESET_ALL}")

    print(f"\n  {Fore.WHITE}-- BROKER INTELLIGENCE --{Style.RESET_ALL}")
    broker_color = Fore.GREEN if "ACCUM" in broker["verdict"] else (Fore.RED if "DISTRIB" in broker["verdict"] else Fore.YELLOW)
    print(f"  Verdict:         {broker_color}{broker['verdict']}{Style.RESET_ALL}")
    print(f"  Net Buyers:      {broker['n_buyers']} brokers")
    print(f"  Net Sellers:     {broker['n_sellers']} brokers")
    if broker["flags"]:
        for flag in broker["flags"]:
            print(f"  {Fore.YELLOW}{flag}{Style.RESET_ALL}")
    mentor_broker_comment(broker["verdict"], broker["n_buyers"], broker["n_sellers"], broker["top_buyer_pct"], broker["top_seller_pct"])

    print(f"\n  {Fore.WHITE}-- FUNDAMENTALS --{Style.RESET_ALL}")
    fund_color = Fore.GREEN if "STRONG" in fund["verdict"] else (Fore.YELLOW if "DECENT" in fund["verdict"] else Fore.RED)
    print(f"  Verdict:         {fund_color}{fund['verdict']}{Style.RESET_ALL}")
    for k, v in fund["details"].items():
        print(f"  {k+':':<18} {v}")

    if unlock_flag:
        print(f"\n  {Fore.RED}? UNLOCK DATE APPROACHING — Promoter shares may be sold{Style.RESET_ALL}")

    print(f"\n  {Fore.WHITE}-- TRADE PLAN --{Style.RESET_ALL}")
    if near_resistance:
        bo_entry = round(resistance * 1.01, 2)
        bo_stop = round(price * 0.95, 2)
        bo_r1 = round(resistance * 1.12, 2)
        bo_r2 = round(resistance * 1.22, 2)
        bo_risk = bo_entry - bo_stop
        bo_reward = bo_r1 - bo_entry
        bo_rr = round(bo_reward / bo_risk, 2) if bo_risk > 0 else 0
        print(f"  ** PRICE NEAR RESISTANCE - Two scenarios **")
        print(f"")
        print(f"  OPTION A - Wait for BREAKOUT above Rs.{resistance:,.2f}")
        print(f"  Entry:           Rs. {bo_entry:,.2f}")
        print(f"  Stop Loss:       Rs. {bo_stop:,.2f}")
        print(f"  Target 1 (40%): Rs. {bo_r1:,.2f}")
        print(f"  Target 2 (40%): Rs. {bo_r2:,.2f}")
        print(f"  Risk/Reward:     {bo_rr:.1f}x")
        print(f"")
        print(f"  OPTION B - Wait for PULLBACK to Rs.{support:,.2f}")
        print(f"  Entry:           Rs. {support:,.2f} - Rs. {round(support*1.02,2):,.2f}")
        print(f"  Stop Loss:       Rs. {stop_loss:,.2f}")
        print(f"  Target 1 (40%): Rs. {target1:,.2f}")
        print(f"  Target 2 (40%): Rs. {target2:,.2f}")
        print(f"  Risk/Reward:     {rr:.1f}x")
        print(f"  ** Do NOT buy at Rs.{price:,.2f} - too close to resistance **")
    else:
        print(f"  Entry Zone:      Rs. {support:,.2f} - Rs. {round(support*1.02,2):,.2f}")
        print(f"  Stop Loss:       Rs. {stop_loss:,.2f} (3% below support)")
        print(f"  Target 1 (40%): Rs. {target1:,.2f}")
        print(f"  Target 2 (40%): Rs. {target2:,.2f}")
        print(f"  Risk/Reward:     {rr:.1f}x")

    if conviction >= 7:
        conv_color = Fore.GREEN
    elif conviction >= 5:
        conv_color = Fore.YELLOW
    else:
        conv_color = Fore.RED

    print(f"\n  {'-'*40}")
    print(f"  CONVICTION SCORE: {conv_color}{conviction}/10{Style.RESET_ALL}")
    if conviction >= 8:
        print(f"  {Fore.GREEN}? HIGH CONVICTION — Strong setup{Style.RESET_ALL}")
    elif conviction >= 6:
        print(f"  {Fore.YELLOW}? MODERATE — Worth watching{Style.RESET_ALL}")
    elif conviction >= 4:
        print(f"  {Fore.YELLOW}? WEAK — Wait for better setup{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}? AVOID — Setup not ready{Style.RESET_ALL}")
    # MENTOR FINAL SUMMARY
    print(f"")
    print(f"  -------------------------------------------------------")
    print(f"  MENTOR OVERALL VERDICT:")
    print(f"")
    
    # Market context
    if conviction >= 8:
        print(f"  STRONG SETUP. All systems aligned.")
    elif conviction >= 6:
        print(f"  DECENT SETUP. Worth watching closely.")
    elif conviction >= 4:
        print(f"  WEAK SETUP. Be patient. Better setups exist.")
    else:
        print(f"  AVOID. Too many things wrong with this stock right now.")
    
    print(f"")
    
    # Technical comment
    if price > latest["ma200"] and price > latest["ma50"]:
        print(f"  TREND: Stock is in a healthy uptrend. Wind is at your back.")
    elif price > latest["ma200"]:
        print(f"  TREND: Long term uptrend intact but short term weak. Wait for recovery.")
    else:
        print(f"  TREND: Stock is in downtrend. Do not buy falling knives.")
    
    # RSI comment
    if 40 <= rsi <= 60:
        print(f"  MOMENTUM: RSI {rsi:.0f} is in sweet spot. Room to move up.")
    elif rsi > 70:
        print(f"  MOMENTUM: RSI {rsi:.0f} is overbought. Do not chase. Wait for pullback.")
    elif rsi < 30:
        print(f"  MOMENTUM: RSI {rsi:.0f} is oversold. Potential bounce but confirm first.")
    
    # Broker comment summary
    if "STRONG ACCUM" in broker["verdict"]:
        print(f"  BROKER: Smart money is buying. You want to be on same side as them.")
    elif "MILD ACCUM" in broker["verdict"]:
        print(f"  BROKER: Some buying interest but not strong conviction yet.")
    elif "DISTRIB" in broker["verdict"]:
        print(f"  BROKER: Smart money is SELLING. Do not buy what institutions are dumping.")
    else:
        print(f"  BROKER: No clear smart money direction. Neutral.")
    
    # Trade action
    print(f"")
    if conviction >= 7 and "ACCUM" in broker["verdict"] and price > latest["ma200"]:
        print(f"  WHAT TO DO: Add to watchlist. Set price alert at entry zone.")
        print(f"  Wait for confirmation candle at support before buying.")
        print(f"  Position size: Use 2% risk rule from Pillar 4.")
    elif conviction >= 5:
        print(f"  WHAT TO DO: Watch only. Do not buy yet.")
        print(f"  Wait for setup to improve before committing capital.")
    else:
        print(f"  WHAT TO DO: Skip this stock. Move to next opportunity.")
    
    if unlock_flag:
        print(f"")
        print(f"  WARNING: Unlock date approaching. Promoter shares may flood")
        print(f"  the market soon. Extra caution required.")
    
    print(f"  -------------------------------------------------------")
    print(f"  {'-'*40}")

# -----------------------------------------------------------
#  MODULE 5 — MARKET SCANNER
# -----------------------------------------------------------

def run_scanner():
    print(f"\n{Fore.CYAN}{'-'*55}")
    print(f"  MODULE 5 — FULL MARKET SCANNER")
    print(f"  Scanning all active stocks...")
    print(f"{'-'*55}{Style.RESET_ALL}")

    symbols = get_all_symbols()
    results = []

    for i, (symbol, sector) in enumerate(symbols):
        try:
            df = get_prices(symbol, 250)
            if len(df) < 60:
                continue
            ok, reason = is_data_quality_ok(df)
            if not ok:
                continue

            df["ma20"] = calc_ma(df["close"], 20)
            df["ma50"] = calc_ma(df["close"], 50)
            df["ma200"] = calc_ma(df["close"], 200)
            df["rsi"] = calc_rsi(df["close"])
            _, _, df["hist"] = calc_macd(df["close"])
            df["vol_avg20"] = df["volume"].rolling(20).mean()

            latest = df.iloc[-1]
            price = latest["close"]
            ma200 = latest["ma200"]
            rsi = latest["rsi"]
            hist = latest["hist"]
            vol_ratio = latest["volume"] / latest["vol_avg20"] if latest["vol_avg20"] > 0 else 1

            # Quick score
            score = 0
            if price > ma200: score += 3
            if 35 <= rsi <= 65: score += 2
            if hist > 0: score += 1
            if vol_ratio > 1.2: score += 1

            # Broker check
            broker = analyze_broker(symbol)
            if "ACCUM" in broker["verdict"]: score += 2
            elif "DISTRIB" in broker["verdict"]: score -= 2

            # Unlock flag
            unlocks = get_unlock_dates(symbol)
            if unlocks: score -= 2

            results.append({
                "symbol": symbol,
                "sector": sector or "N/A",
                "price": price,
                "rsi": round(rsi, 1) if not np.isnan(rsi) else 0,
                "vol_ratio": round(vol_ratio, 1),
                "broker": broker["verdict"],
                "score": score
            })

            # Progress
            if (i + 1) % 20 == 0:
                print(f"  Scanned {i+1}/{len(symbols)} stocks...", end="\r")

        except Exception:
            continue

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    print(f"\n\n  {Fore.GREEN}TOP SETUPS — HIGH CONVICTION{Style.RESET_ALL}")
    print(f"  {'SYMBOL':<12}{'SECTOR':<20}{'PRICE':>8}{'RSI':>7}{'VOL':>6}{'BROKER':<22}{'SCORE':>6}")
    print(f"  {'-'*75}")
    top = [r for r in results if r["score"] >= 7][:15]
    for r in top:
        broker_color = Fore.GREEN if "ACCUM" in r["broker"] else Fore.YELLOW
        print(f"  {Fore.WHITE}{r['symbol']:<12}{Style.RESET_ALL}"
              f"{(r['sector'] or 'N/A'):<20}"
              f"{r['price']:>8.2f}"
              f"{r['rsi']:>7.1f}"
              f"{r['vol_ratio']:>6.1f}x"
              f"  {broker_color}{r['broker']:<20}{Style.RESET_ALL}"
              f"{Fore.GREEN}{r['score']:>6}{Style.RESET_ALL}")

    print(f"\n  {Fore.RED}RED FLAGS — AVOID / EXIT{Style.RESET_ALL}")
    print(f"  {'SYMBOL':<12}{'SECTOR':<20}{'PRICE':>8}{'RSI':>7}{'VOL':>6}{'BROKER':<22}{'SCORE':>6}")
    print(f"  {'-'*75}")
    bottom = [r for r in results if r["score"] <= 2][:10]
    for r in bottom:
        print(f"  {Fore.WHITE}{r['symbol']:<12}{Style.RESET_ALL}"
              f"{(r['sector'] or 'N/A'):<20}"
              f"{r['price']:>8.2f}"
              f"{r['rsi']:>7.1f}"
              f"{r['vol_ratio']:>6.1f}x"
              f"  {Fore.RED}{r['broker']:<20}{Style.RESET_ALL}"
              f"{Fore.RED}{r['score']:>6}{Style.RESET_ALL}")

    print(f"\n  Total stocks scanned: {len(results)}")
    print(f"  High conviction:      {len(top)}")
    print(f"  Red flags:            {len(bottom)}")

# -----------------------------------------------------------
#  MODULE 6 — PORTFOLIO MONITOR
# -----------------------------------------------------------

def monitor_portfolio():
    print(f"\n{Fore.CYAN}{'-'*55}")
    print(f"  MODULE 6 — PORTFOLIO MONITOR")
    print(f"{'-'*55}{Style.RESET_ALL}")

    portfolio = get_portfolio()
    if portfolio.empty:
        print(f"  {Fore.YELLOW}No open positions found.{Style.RESET_ALL}")
        return

    for _, pos in portfolio.iterrows():
        symbol = pos["symbol"]
        qty = pos["quantity"]
        entry = pos["avg_entry_price"]
        stop_pct = pos["hard_stop_pct"] or 7

        df = get_prices(symbol, 60)
        if df.empty:
            continue

        price = df.iloc[-1]["close"]
        pnl_pct = (price - entry) / entry * 100
        stop_price = entry * (1 - stop_pct / 100)

        broker = analyze_broker(symbol)

        # Status
        if price < stop_price:
            status = f"{Fore.RED}?? STOP LOSS BREACHED — EXIT NOW{Style.RESET_ALL}"
        elif "DISTRIB" in broker["verdict"]:
            status = f"{Fore.YELLOW}? BROKER DISTRIBUTION — REVIEW{Style.RESET_ALL}"
        elif pnl_pct > 20:
            status = f"{Fore.GREEN}? STRONG PROFIT — Trail stop{Style.RESET_ALL}"
        elif pnl_pct > 0:
            status = f"{Fore.GREEN}? In profit — Hold{Style.RESET_ALL}"
        else:
            status = f"{Fore.YELLOW}? In loss — Monitor{Style.RESET_ALL}"

        pnl_color = Fore.GREEN if pnl_pct >= 0 else Fore.RED

        print(f"\n  {Fore.WHITE}{'-'*45}{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}{symbol}{Style.RESET_ALL}  |  Qty: {qty}  |  Entry: Rs.{entry:,.2f}")
        print(f"  Current:  Rs.{price:,.2f}  |  P&L: {pnl_color}{pnl_pct:+.1f}%{Style.RESET_ALL}")
        print(f"  Stop:     Rs.{stop_price:,.2f}  |  Broker: {broker['verdict']}")
        print(f"  Status:   {status}")

# -----------------------------------------------------------
#  MAIN MENU
# -----------------------------------------------------------

def main():
    while True:
        print(f"\n{Fore.CYAN}{'-'*55}")
        check_data_freshness()
        print(f"   NEPSE INTELLIGENCE ENGINE")
        print(f"   5-Pillar Analysis System")
        print(f"   {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'-'*55}{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}1.{Style.RESET_ALL} Market Regime Analysis")
        print(f"  {Fore.WHITE}2.{Style.RESET_ALL} Full Market Scanner (All Stocks)")
        print(f"  {Fore.WHITE}3.{Style.RESET_ALL} Individual Stock Analysis")
        print(f"  {Fore.WHITE}4.{Style.RESET_ALL} Portfolio Monitor")
        print(f"  {Fore.WHITE}5.{Style.RESET_ALL} Broker Intelligence (Single Stock)")
        print(f"  {Fore.WHITE}0.{Style.RESET_ALL} Exit")
        print(f"\n  Enter choice: ", end="")

        choice = input().strip()

        if choice == "1":
            analyze_market_regime()
        elif choice == "2":
            run_scanner()
        elif choice == "3":
            print("  Enter stock symbol (e.g. NABIL): ", end="")
            sym = input().strip().upper()
            analyze_stock(sym)
        elif choice == "4":
            monitor_portfolio()
        elif choice == "5":
            print("  Enter stock symbol: ", end="")
            sym = input().strip().upper()
            b = analyze_broker(sym)
            print(f"\n  Broker Verdict:  {b['verdict']}")
            print(f"  Net Buyers:      {b['n_buyers']} brokers")
            print(f"  Net Sellers:     {b['n_sellers']} brokers")
            print(f"  Top Buyer Conc:  {b['top_buyer_pct']:.1f}%")
            print(f"  Top Seller Conc: {b['top_seller_pct']:.1f}%")
            mentor_broker_comment(b["verdict"], b["n_buyers"], b["n_sellers"], b["top_buyer_pct"], b["top_seller_pct"])
            for flag in b["flags"]:
                print(f"  {Fore.YELLOW}{flag}{Style.RESET_ALL}")
        elif choice == "0":
            print(f"\n  {Fore.CYAN}Goodbye.{Style.RESET_ALL}\n")
            break
        else:
            print(f"  {Fore.RED}Invalid choice.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
