import sqlite3
import datetime
import re
from rich.console import Console
from rich.table import Table
from rich.rule import Rule
from rich.panel import Panel
from rich import box
from rich.text import Text

WHALES = {'14', '20', '32', '49', '58', '75'}

WHALE_NAMES = {
    '14': 'Nepal Stock House',
    '20': 'Sipla Securities',
    '32': 'Premier Securities',
    '49': 'Online Securities',
    '58': 'Naasa Securities',
    '75': 'NIMB Stock Markets'
}

REGULATED_SECTORS = {
    'Commercial Banks',
    'Development Banks',
    'Life Insurance',
    'Non Life Insurance'
}

SECTOR_SCORE = {
    'Microfinance': 15,
    'Manufacturing And Processing': 13,
    'Others': 13,
    'Non Life Insurance': 11,
    'Hotels And Tourism': 10,
    'Investment': 9,
    'Hydro Power': 8,
    'Life Insurance': 7,
    'Development Banks': 6,
    'Finance': 5,
    'Commercial Banks': 2,
}

SECTOR_CEILING = {
    'Microfinance': 'Rs 3000-6000+',
    'Manufacturing And Processing': 'Rs 1500-5000',
    'Others': 'Rs 1000-2000',
    'Non Life Insurance': 'Rs 800-2500',
    'Hotels And Tourism': 'Rs 800-1500',
    'Investment': 'Rs 1000-1500',
    'Hydro Power': 'Rs 800-1500',
    'Life Insurance': 'Rs 800-2500',
    'Development Banks': 'Rs 1000-2000',
    'Finance': 'Rs 600-1200',
    'Commercial Banks': 'Rs 300-500',
}


def get_broker_analysis(symbol, conn):
    brokers = conn.execute("""
        SELECT broker_id,
               COALESCE(broker_name, 'Unknown') as bname,
               SUM(buy_val) as tbuy,
               SUM(sell_val) as tsell,
               SUM(net_val) as net,
               COUNT(DISTINCT date) as days
        FROM broker_activity
        WHERE symbol=?
        GROUP BY broker_id
        ORDER BY net DESC
    """, (symbol,)).fetchall()

    if not brokers:
        return None

    buyers  = [b for b in brokers if b[4] and b[4] > 0]
    sellers = [b for b in brokers if b[4] and b[4] < 0]

    whale_buyers  = [b for b in brokers if str(b[0]) in WHALES and b[4] and b[4] > 0]
    whale_sellers = [b for b in brokers if str(b[0]) in WHALES and b[4] and b[4] < 0]

    total_buy  = sum(b[2] or 0 for b in brokers)
    total_sell = sum(b[3] or 0 for b in brokers)

    # Consecutive buy days
    daily = conn.execute("""
        SELECT date, SUM(net_val) as day_net
        FROM broker_activity
        WHERE symbol=?
        GROUP BY date
        ORDER BY date DESC
    """, (symbol,)).fetchall()

    consec_buy = 0
    consec_sell = 0
    for d in daily:
        if d[1] and d[1] > 0:
            if consec_sell == 0:
                consec_buy += 1
        else:
            if consec_buy == 0:
                consec_sell += 1
            break

    # Broker score
    wb = len(whale_buyers)
    ws = len(whale_sellers)
    whale_diff = wb - ws

    if whale_diff >= 3:
        broker_score = 90
    elif whale_diff == 2:
        broker_score = 75
    elif whale_diff == 1:
        broker_score = 60
    elif whale_diff == 0:
        broker_score = 45
    elif whale_diff == -1:
        broker_score = 30
    elif whale_diff == -2:
        broker_score = 20
    else:
        broker_score = 10

    # Adjust for consecutive buys
    broker_score = min(100, broker_score + consec_buy * 2)

    return {
        'buyers': buyers[:3],
        'sellers': sellers[-3:],
        'whale_buyers': whale_buyers,
        'whale_sellers': whale_sellers,
        'broker_score': broker_score,
        'consec_buy': consec_buy,
        'consec_sell': consec_sell,
        'total_volume': total_buy,
        'wb': wb,
        'ws': ws,
    }


def calc_score(pub_shares, sector, days_left, broker_score, phase, pct_from_list, pct_from_ath):
    # Float score (30 pts)
    if pub_shares and pub_shares < 500_000:
        float_score = 30
    elif pub_shares and pub_shares < 1_000_000:
        float_score = 26
    elif pub_shares and pub_shares < 2_000_000:
        float_score = 21
    elif pub_shares and pub_shares < 4_000_000:
        float_score = 15
    elif pub_shares and pub_shares < 8_000_000:
        float_score = 8
    else:
        float_score = 3

    # Sector score (15 pts)
    sec_score = SECTOR_SCORE.get(sector, 5)

    # Runway score (20 pts) — regulated sectors get fixed 15
    if sector in REGULATED_SECTORS:
        runway_score = 15
    else:
        if days_left > 900:
            runway_score = 20
        elif days_left > 600:
            runway_score = 17
        elif days_left > 365:
            runway_score = 14
        elif days_left > 180:
            runway_score = 8
        elif days_left > 90:
            runway_score = 3
        else:
            runway_score = 0

    # Broker score (20 pts)
    bscore = int(broker_score / 100 * 20) if broker_score else 0

    # Phase score (15 pts)
    phase_map = {
        'FRESH': 13,
        'ACCUMULATION': 15,
        'EARLY RUN': 10,
        'MID RUN': 6,
        'NEAR ATH': 3,
        'DISTRIBUTION': 0,
    }
    phase_score = phase_map.get(phase, 5)

    total = float_score + sec_score + runway_score + bscore + phase_score
    return min(total, 100), float_score, sec_score, runway_score, bscore, phase_score


def detect_phase(list_price, cur_price, ath, days_listed, broker_score):
    if not list_price or not cur_price or list_price == 0:
        return 'UNKNOWN'

    pct_from_list = (cur_price - list_price) / list_price * 100
    pct_from_ath  = (cur_price - ath) / ath * 100 if ath else 0

    if days_listed < 30:
        return 'FRESH'
    elif pct_from_ath < -35 and broker_score and broker_score < 40:
        return 'DISTRIBUTION'
    elif pct_from_ath > -15:
        return 'NEAR ATH'
    elif pct_from_list < 30 and pct_from_ath < -20:
        return 'ACCUMULATION'
    elif pct_from_list > 100 and pct_from_ath < -25:
        return 'EARLY RUN'
    else:
        return 'MID RUN'


def analyze_ipo_tracker(db_path='nepse_market_data.db'):
    console = Console(width=130)
    conn = sqlite3.connect(db_path)
    today = datetime.date.today()

    console.print()
    console.rule('[bold cyan]Option 46 — IPO Intelligence Center[/bold cyan]', style='cyan')
    console.print()

    # Get all IPO stocks
    cutoff = (today - datetime.timedelta(days=1095)).strftime('%Y-%m-%d')
    stocks = conn.execute("""
        SELECT
            sp.symbol,
            MIN(sp.date) as list_date,
            COUNT(DISTINCT sp.date) as trading_days,
            c.sector,
            f.public_shares,
            f.promoter_pct,
            f.public_pct,
            u.unlock_date,
            (SELECT close FROM stock_prices WHERE symbol=sp.symbol ORDER BY date ASC LIMIT 1) as list_price,
            (SELECT MAX(close) FROM stock_prices WHERE symbol=sp.symbol) as ath,
            (SELECT date FROM stock_prices WHERE symbol=sp.symbol ORDER BY close DESC LIMIT 1) as ath_date,
            (SELECT close FROM stock_prices WHERE symbol=sp.symbol ORDER BY date DESC LIMIT 1) as cur_price
        FROM stock_prices sp
        INNER JOIN companies c ON sp.symbol = c.symbol
        LEFT JOIN fundamentals f ON sp.symbol = f.symbol
        LEFT JOIN unlock_dates u ON sp.symbol = u.symbol
        WHERE c.sector IN (
            'Commercial Banks','Development Banks','Finance',
            'Hotels And Tourism','Hydro Power','Investment',
            'Life Insurance','Manufacturing And Processing',
            'Microfinance','Non Life Insurance','Others','Tradings'
        )
        GROUP BY sp.symbol
        HAVING MIN(sp.date) >= ?
        AND COUNT(DISTINCT sp.date) >= 5
        ORDER BY MIN(sp.date) DESC
    """, (cutoff,)).fetchall()

    # Filter non-equity
    equity = []
    for r in stocks:
        sym = r[0]
        if re.search(r'(D8[0-9]|D9[0-9]|B8[0-9]|B9[0-9]|LD8|LD9|BD8|BD9)', sym): continue
        if re.search(r'(MF[0-9]?$|F[123]$)', sym): continue
        if re.search(r'(PO$|PNP$)', sym): continue
        if re.search(r'(207[0-9]|208[0-9]|209[0-9])', sym): continue
        if '/' in sym: continue
        if len(sym) > 9: continue
        if sym in conn.execute("SELECT symbol FROM companies WHERE sector IS NULL").fetchall(): continue
        equity.append(r)

    # Process each stock
    results = []
    danger  = []
    unlocked = []

    for r in equity:
        sym, list_date, days, sector, pub_shares, prom_pct, pub_pct, unlock_date, list_price, ath, ath_date, cur = r

        if not list_price or not cur:
            continue

        # Unlock date
        if unlock_date:
            try:
                ud = datetime.date.fromisoformat(unlock_date)
                calculated = False
            except:
                ld = datetime.date.fromisoformat(list_date)
                ud = datetime.date(ld.year+3, ld.month, ld.day)
                calculated = True
        else:
            ld = datetime.date.fromisoformat(list_date)
            try:
                ud = datetime.date(ld.year+3, ld.month, ld.day)
            except:
                ud = datetime.date(ld.year+3, ld.month, min(ld.day, 28))
            calculated = True

        days_left = (ud - today).days

        # Skip unlocked non-regulated sectors
        is_unlocked = days_left < 0 and sector not in REGULATED_SECTORS

        # Broker analysis
        ba = get_broker_analysis(sym, conn)
        broker_score = ba['broker_score'] if ba else 50

        # Phase
        pct_from_list = (cur - list_price) / list_price * 100 if list_price else 0
        pct_from_ath  = (cur - ath) / ath * 100 if ath else 0
        phase = detect_phase(list_price, cur, ath, days, broker_score)

        # Score
        score, fs, ss, rs, bs, ps = calc_score(
            pub_shares, sector, days_left, broker_score,
            phase, pct_from_list, pct_from_ath
        )

        entry = {
            'sym': sym, 'list_date': list_date, 'days': days,
            'sector': sector, 'pub_shares': pub_shares,
            'prom_pct': prom_pct, 'pub_pct': pub_pct,
            'unlock_date': ud, 'days_left': days_left,
            'calculated': calculated,
            'list_price': list_price, 'ath': ath,
            'ath_date': ath_date, 'cur': cur,
            'pct_from_list': pct_from_list,
            'pct_from_ath': pct_from_ath,
            'phase': phase, 'broker_score': broker_score,
            'score': score, 'fs': fs, 'ss': ss, 'rs': rs,
            'bs': bs, 'ps': ps, 'ba': ba,
            'is_unlocked': is_unlocked,
        }

        if is_unlocked:
            unlocked.append(entry)
        elif days_left >= 0 and days_left < 180 and sector not in REGULATED_SECTORS:
            danger.append(entry)
        else:
            results.append(entry)

    results.sort(key=lambda x: x['score'], reverse=True)
    danger.sort(key=lambda x: x['days_left'])

    # ── SECTION A: OPPORTUNITY SCANNER ───────────────────────────────────────
    console.rule('[bold green]🔥 SECTION A — Opportunity Scanner[/bold green]', style='green')
    console.print(f'  [dim]IPO stocks ranked by composite score — higher = better opportunity[/dim]')
    console.print()

    t = Table(box=box.SIMPLE, header_style='bold green', show_edge=False, padding=(0,1))
    t.add_column('#',           width=3,  justify='right')
    t.add_column('Symbol',      width=9)
    t.add_column('Sector',      width=22)
    t.add_column('Float',       width=10, justify='right')
    t.add_column('Prom%',       width=7,  justify='right')
    t.add_column('Phase',       width=14)
    t.add_column('From List',   width=10, justify='right')
    t.add_column('From ATH',    width=10, justify='right')
    t.add_column('Unlock',      width=10, justify='right')
    t.add_column('Broker',      width=8,  justify='right')
    t.add_column('Score',       width=7,  justify='right')
    t.add_column('Signal',      width=14)

    for i, e in enumerate(results[:25], 1):
        # Colors
        phase_color = {
            'FRESH': 'cyan', 'ACCUMULATION': 'green',
            'EARLY RUN': 'yellow', 'MID RUN': 'white',
            'NEAR ATH': 'magenta', 'DISTRIBUTION': 'red'
        }.get(e['phase'], 'white')

        score_color = 'green' if e['score'] >= 70 else 'yellow' if e['score'] >= 50 else 'red'

        if e['score'] >= 75:
            signal = '[bold green]🔥 PRIME[/bold green]'
        elif e['score'] >= 60:
            signal = '[green]✅ WATCH[/green]'
        elif e['score'] >= 45:
            signal = '[yellow]⚠️ HOLD[/yellow]'
        else:
            signal = '[red]❌ AVOID[/red]'

        pub_str  = f"{e['pub_shares']/1e3:.0f}K" if e['pub_shares'] else 'N/A'
        prom_str = f"{e['prom_pct']:.0f}%" if e['prom_pct'] else 'N/A'
        ceil = SECTOR_CEILING.get(e['sector'], '?')

        unlock_str = f"{e['days_left']}d" if e['days_left'] >= 0 else 'REG'
        unlock_color = 'green' if e['days_left'] > 365 else 'yellow' if e['days_left'] > 90 else 'red'

        t.add_row(
            str(i),
            f"[bold]{e['sym']}[/bold]",
            e['sector'][:21],
            pub_str,
            prom_str,
            f"[{phase_color}]{e['phase']}[/{phase_color}]",
            f"[green]+{e['pct_from_list']:.0f}%[/green]" if e['pct_from_list'] >= 0 else f"[red]{e['pct_from_list']:.0f}%[/red]",
            f"[red]{e['pct_from_ath']:.0f}%[/red]",
            f"[{unlock_color}]{unlock_str}[/{unlock_color}]",
            f"{e['broker_score']}/100",
            f"[{score_color}]{e['score']}[/{score_color}]",
            signal,
        )

    console.print(t)

    # Score legend
    console.print(Panel(
        '[bold]Score Breakdown:[/bold] Float(30) + Sector(15) + Runway(20) + Broker(20) + Phase(15)\n'
        '[green]75+[/green] PRIME  [green]60-74[/green] WATCH  [yellow]45-59[/yellow] HOLD  [red]<45[/red] AVOID\n'
        '[bold]Phase:[/bold] ACCUMULATION=best entry | FRESH=just listed | EARLY RUN=still room | NEAR ATH=careful',
        title='How to read this table',
        border_style='dim'
    ))

    # ── SECTION B: BROKER INTELLIGENCE ───────────────────────────────────────
    console.print()
    console.rule('[bold blue]🏦 SECTION B — Broker Intelligence (Top 10 Opportunities)[/bold blue]', style='blue')
    console.print()

    for e in results[:10]:
        ba = e['ba']
        if not ba:
            continue

        wb = ba['wb']
        ws = ba['ws']

        if wb > ws:
            verdict_color = 'green'
            verdict = f'ACCUMULATING ({wb} whale buyers vs {ws} sellers)'
        elif ws > wb:
            verdict_color = 'red'
            verdict = f'DISTRIBUTING ({ws} whale sellers vs {wb} buyers)'
        else:
            verdict_color = 'yellow'
            verdict = f'NEUTRAL ({wb} whale buyers = {ws} sellers)'

        console.print(f"  [bold]{e['sym']}[/bold] — [{verdict_color}]{verdict}[/{verdict_color}]  Vol: Rs{ba['total_volume']/1e6:.1f}M")

        if ba['buyers']:
            console.print(f"    [green]TOP BUYERS:[/green]")
            for b in ba['buyers'][:3]:
                bid, bname, tbuy, tsell, net, days = b
                whale = ' 🐋' if str(bid) in WHALES else ''
                console.print(f"      Broker {str(bid):>3} | {str(bname)[:30]:<30} | +Rs{net/1e6:.2f}M | {days}d{whale}")

        if ba['sellers']:
            console.print(f"    [red]TOP SELLERS:[/red]")
            for b in list(reversed(ba['sellers']))[:3]:
                bid, bname, tbuy, tsell, net, days = b
                whale = ' 🐋' if str(bid) in WHALES else ''
                console.print(f"      Broker {str(bid):>3} | {str(bname)[:30]:<30} | -Rs{abs(net)/1e6:.2f}M | {days}d{whale}")

        console.print()

    # ── SECTION C: DANGER ZONE ────────────────────────────────────────────────
    console.print()
    console.rule('[bold red]⚠️  SECTION C — Danger Zone (Unlock < 180 days)[/bold red]', style='red')
    console.print(f'  [dim]High-risk sectors only — Hydro, Microfinance, Manufacturing, Others, Hotels[/dim]')
    console.print()

    t2 = Table(box=box.SIMPLE, header_style='bold red', show_edge=False)
    t2.add_column('Symbol',     width=9)
    t2.add_column('Sector',     width=22)
    t2.add_column('Unlock',     width=12)
    t2.add_column('Days Left',  width=10, justify='right')
    t2.add_column('Pub Shares', width=12, justify='right')
    t2.add_column('Price',      width=10, justify='right')
    t2.add_column('From ATH',   width=10, justify='right')
    t2.add_column('Broker',     width=8,  justify='right')
    t2.add_column('Action',     width=18)

    for e in danger:
        if e['days_left'] < 30:
            action = '[bold red]EXIT NOW[/bold red]'
            color  = 'red'
        elif e['days_left'] < 90:
            action = '[red]REDUCE POSITION[/red]'
            color  = 'red'
        else:
            action = '[yellow]TIGHTEN STOP[/yellow]'
            color  = 'yellow'

        pub_str = f"{e['pub_shares']/1e3:.0f}K" if e['pub_shares'] else 'N/A'

        t2.add_row(
            f"[bold]{e['sym']}[/bold]",
            e['sector'][:21],
            str(e['unlock_date']),
            f"[{color}]{e['days_left']}d[/{color}]",
            pub_str,
            f"Rs {e['cur']:,.0f}",
            f"{e['pct_from_ath']:.0f}%",
            f"{e['broker_score']}/100",
            action,
        )

    console.print(t2)

    # ── SECTION D: PERFORMANCE SUMMARY ───────────────────────────────────────
    console.print()
    console.rule('[bold magenta]📊 SECTION D — IPO Performance Summary[/bold magenta]', style='magenta')
    console.print()

    # By float size
    console.print('  [bold]Returns by Float Size:[/bold]')
    float_buckets = [
        ('< 500K shares',   0,       500_000),
        ('500K - 1M',       500_000, 1_000_000),
        ('1M - 2M',         1_000_000, 2_000_000),
        ('2M - 4M',         2_000_000, 4_000_000),
        ('> 4M shares',     4_000_000, 999_000_000),
    ]

    all_stocks = results + danger + unlocked
    for label, lo, hi in float_buckets:
        bucket = [e for e in all_stocks if e['pub_shares'] and lo <= e['pub_shares'] < hi]
        if not bucket:
            continue
        returns = [e['pct_from_list'] for e in bucket]
        avg_ret = sum(returns) / len(returns)
        max_ret = max(returns)
        color = 'green' if avg_ret > 100 else 'yellow' if avg_ret > 50 else 'white'
        console.print(f"    [{color}]{label:<18}[/{color}]  {len(bucket):>3} stocks  avg +{avg_ret:.0f}%  best +{max_ret:.0f}%")

    console.print()

    # By sector
    console.print('  [bold]Returns by Sector:[/bold]')
    sectors_seen = {}
    for e in all_stocks:
        s = e['sector']
        if s not in sectors_seen:
            sectors_seen[s] = []
        sectors_seen[s].append(e['pct_from_list'])

    for s, rets in sorted(sectors_seen.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True):
        avg = sum(rets) / len(rets)
        best = max(rets)
        color = 'green' if avg > 150 else 'yellow' if avg > 50 else 'white'
        console.print(f"    [{color}]{s[:28]:<28}[/{color}]  {len(rets):>3} IPOs  avg +{avg:.0f}%  best +{best:.0f}%")

    console.print()

    # Top 5 all time performers
    console.print('  [bold]Top 5 IPO Performers (from listing price):[/bold]')
    top5 = sorted(all_stocks, key=lambda x: x['pct_from_list'], reverse=True)[:5]
    for i, e in enumerate(top5, 1):
        console.print(f"    {i}. [bold green]{e['sym']:<8}[/bold green] +{e['pct_from_list']:.0f}% | {e['sector']} | Float: {e['pub_shares']/1e3:.0f}K shares" if e['pub_shares'] else f"    {i}. {e['sym']} +{e['pct_from_list']:.0f}%")

    # ── SECTION E: UNLOCKED ───────────────────────────────────────────────────
    if unlocked:
        console.print()
        console.rule('[bold dim]🔓 SECTION E — Unlocked Stocks (Past 3 Year Lock-in)[/bold dim]', style='dim')
        console.print('  [dim]These trade as normal stocks now — no IPO supply advantage[/dim]')
        console.print()

        t3 = Table(box=box.SIMPLE, header_style='dim', show_edge=False)
        t3.add_column('Symbol',     width=9)
        t3.add_column('Sector',     width=22)
        t3.add_column('Listed',     width=12)
        t3.add_column('Unlocked',   width=12)
        t3.add_column('From List%', width=11, justify='right')
        t3.add_column('From ATH%',  width=11, justify='right')
        t3.add_column('Price',      width=10, justify='right')

        unlocked.sort(key=lambda x: x['pct_from_list'], reverse=True)
        for e in unlocked[:20]:
            ret_color = 'green' if e['pct_from_list'] > 0 else 'red'
            t3.add_row(
                e['sym'],
                e['sector'][:21],
                e['list_date'],
                str(e['unlock_date']),
                f"[{ret_color}]+{e['pct_from_list']:.0f}%[/{ret_color}]",
                f"{e['pct_from_ath']:.0f}%",
                f"Rs {e['cur']:,.0f}",
            )
        console.print(t3)

    conn.close()
    console.print()
