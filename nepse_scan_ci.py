import os, json, datetime, logging
from nepse import Nepse

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)

def get_nepse():
    n = Nepse()
    n.setTLSVerification(False)
    return n

def is_market_open(n):
    try:
        status = n.getMarketStatus()
        return status.get('isOpen') == 'OPEN'
    except Exception as e:
        log.error('Market status error: ' + str(e))
        return False

def fetch_broker_data(n):
    try:
        log.info('Fetching floorsheet...')
        fs = n.getFloorSheet()
        if fs is None:
            log.error('Floorsheet returned None')
            return None
        import pandas as pd
        df = fs if isinstance(fs, pd.DataFrame) else pd.DataFrame(fs)
        if df.empty:
            log.error('Floorsheet is empty')
            return None
        log.info('Floorsheet rows: ' + str(len(df)))
        col_map = {}
        for c in df.columns:
            cl = c.lower()
            if cl in ('buyermemberid', 'buyerbrokerid', 'buyerbroker'): col_map[c] = 'buyer_broker'
            elif cl in ('sellermemberid', 'sellerbrokerid', 'sellerbroker'): col_map[c] = 'seller_broker'
            elif cl in ('stocksymbol', 'symbol', 'scrip'): col_map[c] = 'symbol'
            elif cl in ('contractamount', 'amount', 'value'): col_map[c] = 'amount'
            elif cl in ('contractquantity', 'quantity', 'qty'): col_map[c] = 'quantity'
        df = df.rename(columns=col_map)
        required = ['symbol','buyer_broker','seller_broker','amount']
        missing = [r for r in required if r not in df.columns]
        if missing:
            log.error('Missing columns: ' + str(missing))
            log.error('Available: ' + str(list(df.columns)))
            return None
        broker_data = {}
        for _, row in df.iterrows():
            sym = str(row.get('symbol','')).strip()
            buyer = str(row.get('buyer_broker','')).strip()
            seller = str(row.get('seller_broker','')).strip()
            amt = float(row.get('amount', 0) or 0)
            if not sym: continue
            if sym not in broker_data:
                broker_data[sym] = {}
            if buyer:
                broker_data[sym][buyer] = broker_data[sym].get(buyer, 0) + amt
            if seller:
                broker_data[sym][seller] = broker_data[sym].get(seller, 0) - amt
        log.info('Processed ' + str(len(broker_data)) + ' symbols')
        return broker_data
    except Exception as e:
        log.error('Fetch error: ' + str(e))
        import traceback; traceback.print_exc()
        return None

def save_broker_json(broker_data, date_str):
    os.makedirs('daily_data', exist_ok=True)
    path = 'daily_data/broker_' + date_str + '.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'date': date_str, 'brokers': broker_data}, f)
    log.info('Saved: ' + path)
    return path

def fetch_price_data(n):
    try:
        import pandas as pd
        log.info("Fetching live market prices...")
        data = n.getLiveMarket()
        if data is None:
            log.error("getLiveMarket returned None")
            return None
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        if df.empty:
            log.error("Live market empty")
            return None
        log.info("Live market rows: " + str(len(df)))
        # Normalize columns
        col_map = {}
        for c in df.columns:
            cl = c.lower()
            if cl in ("symbol", "stocksymbol", "scrip"): col_map[c] = "symbol"
            elif cl in ("lasttradedprice", "ltp", "closeprice", "close"): col_map[c] = "close"
            elif cl in ("openprice", "open"): col_map[c] = "open"
            elif cl in ("highprice", "high"): col_map[c] = "high"
            elif cl in ("lowprice", "low"): col_map[c] = "low"
            elif cl in ("totaltradedquantity", "totaltradeQuantity", "volume", "qty"): col_map[c] = "volume"
        df = df.rename(columns=col_map)
        required = ["symbol", "close"]
        if not all(c in df.columns for c in required):
            log.error("Missing required cols. Available: " + str(list(df.columns)))
            return None
        for col in ["close", "open", "high", "low", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df = df[df["close"] > 0]
        prices = []
        for _, row in df.iterrows():
            sym = str(row.get("symbol", "")).strip()
            if not sym:
                continue
            prices.append({
                "symbol": sym,
                "open":   float(row.get("open",   row["close"])),
                "high":   float(row.get("high",   row["close"])),
                "low":    float(row.get("low",    row["close"])),
                "close":  float(row["close"]),
                "volume": float(row.get("volume", 0)),
            })
        log.info("Processed " + str(len(prices)) + " price rows")
        return prices
    except Exception as e:
        log.error("Price fetch error: " + str(e))
        import traceback; traceback.print_exc()
        return None

def save_price_json(prices, date_str):
    os.makedirs("daily_data", exist_ok=True)
    path = "daily_data/prices_" + date_str + ".json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"date": date_str, "prices": prices}, f)
    log.info("Saved: " + path)
    return path

def main():
    today = datetime.date.today().isoformat()
    log.info("NEPSE Daily Scan CI - " + today)
    n = get_nepse()
    broker_data = fetch_broker_data(n)
    if broker_data is None:
        log.error("No broker data - market may be closed or API unavailable")
        return
    path = save_broker_json(broker_data, today)
    log.info("Done: " + path)
    prices = fetch_price_data(n)
    if prices:
        save_price_json(prices, today)
    else:
        log.warning("No price data saved")

if __name__ == '__main__':
    main()
