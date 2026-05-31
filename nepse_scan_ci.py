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
            if 'buyer' in cl and 'broker' in cl: col_map[c] = 'buyer_broker'
            elif 'seller' in cl and 'broker' in cl: col_map[c] = 'seller_broker'
            elif 'symbol' in cl or 'scrip' in cl: col_map[c] = 'symbol'
            elif 'amount' in cl or 'value' in cl: col_map[c] = 'amount'
            elif 'quantity' in cl or 'qty' in cl: col_map[c] = 'quantity'
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

def main():
    today = datetime.date.today().isoformat()
    log.info('NEPSE Daily Scan CI - ' + today)
    n = get_nepse()
    broker_data = fetch_broker_data(n)
    if broker_data is None:
        log.error('No broker data - market may be closed or API unavailable')
        return
    path = save_broker_json(broker_data, today)
    log.info('Done: ' + path)

if __name__ == '__main__':
    main()
