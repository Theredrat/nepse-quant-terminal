import shutil, ast

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_broker_logger.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

# Check if already defined
if '_ensure_broker_activity_table' in content:
    print('Already installed — nothing to do')
    exit()

NEW_FUNCS = '''
def _ensure_broker_activity_table(db_path='nepse_market_data.db'):
    import sqlite3
    conn = sqlite3.connect(db_path)
    sql = (
        "CREATE TABLE IF NOT EXISTS broker_activity ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "symbol TEXT NOT NULL, date TEXT NOT NULL, broker_id TEXT NOT NULL, "
        "broker_name TEXT, buy_qty INTEGER DEFAULT 0, sell_qty INTEGER DEFAULT 0, "
        "net_qty INTEGER DEFAULT 0, buy_val REAL DEFAULT 0.0, sell_val REAL DEFAULT 0.0, "
        "net_val REAL DEFAULT 0.0, UNIQUE(symbol, date, broker_id))"
    )
    conn.execute(sql)
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ba_symbol_date ON broker_activity(symbol, date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ba_date ON broker_activity(date)')
    conn.commit()
    conn.close()


def log_broker_activity(fs_df, db_path='nepse_market_data.db'):
    try:
        import sqlite3, pandas as pd
        from datetime import date, timedelta
        if fs_df is None or fs_df.empty:
            return
        _ensure_broker_activity_table(db_path)
        buy = (
            fs_df.groupby(['symbol', 'buyer_broker'])
            .agg(buy_qty=('quantity', 'sum'), buy_val=('amount', 'sum'), broker_name=('buyerBrokerName', 'first'))
            .reset_index().rename(columns={'buyer_broker': 'broker_id'})
        )
        sell = (
            fs_df.groupby(['symbol', 'seller_broker'])
            .agg(sell_qty=('quantity', 'sum'), sell_val=('amount', 'sum'), broker_name_s=('sellerBrokerName', 'first'))
            .reset_index().rename(columns={'seller_broker': 'broker_id'})
        )
        merged = pd.merge(buy, sell, on=['symbol', 'broker_id'], how='outer').fillna(0)
        if 'broker_name_s' in merged.columns:
            merged['broker_name'] = merged.apply(
                lambda r: r['broker_name'] if r['broker_name'] not in (0, '', None) else r['broker_name_s'], axis=1
            )
        trade_date = str(fs_df['businessDate'].iloc[0])[:10]
        records = []
        for _, row in merged.iterrows():
            bid_raw = str(row['broker_id']).replace('.0', '')
            bid = bid_raw if bid_raw.isdigit() else str(row['broker_id'])
            bq = int(row.get('buy_qty', 0) or 0)
            sq = int(row.get('sell_qty', 0) or 0)
            bv = float(row.get('buy_val', 0) or 0)
            sv = float(row.get('sell_val', 0) or 0)
            records.append((str(row['symbol']), trade_date, bid,
                str(row.get('broker_name', '') or ''), bq, sq, bq-sq, bv, sv, bv-sv))
        if not records:
            return
        conn = sqlite3.connect(db_path)
        upsert = (
            "INSERT INTO broker_activity "
            "(symbol,date,broker_id,broker_name,buy_qty,sell_qty,net_qty,buy_val,sell_val,net_val) "
            "VALUES (?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(symbol,date,broker_id) DO UPDATE SET "
            "broker_name=excluded.broker_name, buy_qty=excluded.buy_qty, sell_qty=excluded.sell_qty, "
            "net_qty=excluded.net_qty, buy_val=excluded.buy_val, sell_val=excluded.sell_val, "
            "net_val=excluded.net_val"
        )
        conn.executemany(upsert, records)
        cutoff = (date.today() - timedelta(days=3*365)).strftime('%Y-%m-%d')
        deleted = conn.execute('DELETE FROM broker_activity WHERE date < ?', (cutoff,)).rowcount
        conn.commit()
        total_rows = conn.execute('SELECT COUNT(*) FROM broker_activity').fetchone()[0]
        distinct_dates = conn.execute('SELECT COUNT(DISTINCT date) FROM broker_activity').fetchone()[0]
        conn.close()
        stocks_logged = len(merged['symbol'].unique())
        clean_msg = f'  (cleaned {deleted} old records)' if deleted > 0 else ''
        print(
            f'  Broker activity saved — {stocks_logged} stocks, {len(records)} broker rows '
            f'logged for {trade_date}{clean_msg}  '
            f'[{total_rows:,} total rows, {distinct_dates} trading days in history]'
        )
    except Exception as e:
        print(f'  [broker logger] Warning: {e}')

'''

# Insert the definitions just before the if __name__ block
idx = content.rfind('\nif __name__')
if idx == -1:
    idx = len(content)
content = content[:idx] + NEW_FUNCS + content[idx:]

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK — both functions installed successfully')
    print('_ensure_broker_activity_table: defined')
    print('log_broker_activity: defined')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_broker_logger.py', 'nepse_scanner.py')
    print('Backup restored — scanner unchanged')
