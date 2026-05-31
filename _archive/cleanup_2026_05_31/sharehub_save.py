import os, csv, re

os.makedirs("sharehub_data", exist_ok=True)

def parse_nepali_amount(s):
    """Convert Rs. 1.73 Arab, Rs. 63.84 Cr, Rs. 40.67 L etc to float"""
    s = s.strip()
    try:
        if "Arab" in s:
            return float(re.sub(r"[^\d.]", "", s.replace("Arab","").strip())) * 1e9
        elif "Cr" in s:
            return float(re.sub(r"[^\d.]", "", s.replace("Cr","").strip())) * 1e7
        elif "L" in s:
            return float(re.sub(r"[^\d.]", "", s.replace("L","").strip())) * 1e5
        elif "K" in s:
            return float(re.sub(r"[^\d.]", "", s.replace("K","").strip())) * 1e3
        else:
            return float(re.sub(r"[^\d.-]", "", s))
    except:
        return 0.0

def parse_data_line(line):
    """
    Parse a joined data line like:
    22,53,123Rs. 63.84 Cr51,97,305Rs. 1.73 ArabRs. 332.938,3685.47...
    Pattern: vol amt vol amt avg_price trans pct vol amt avg_price trans pct ratio vol amt trans
    """
    # Split on Rs. boundaries and number boundaries
    # Use regex to extract all tokens
    tokens = re.findall(
        r'Rs\.\s*[\d,.]+\s*(?:Arab|Cr|L|K)?|[\d,.]+',
        line
    )
    
    cleaned = []
    for t in tokens:
        t = t.strip()
        if t.startswith("Rs."):
            cleaned.append(str(parse_nepali_amount(t.replace("Rs.", "").strip())))
        else:
            # Remove commas from numbers like 22,53,123
            cleaned.append(t.replace(",", ""))
    
    return cleaned

def save_stock_data(symbol, raw_text):
    lines = [l.strip() for l in raw_text.strip().splitlines()]
    
    rows = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Broker ID line - just a number
        if re.match(r'^\d+$', line):
            broker_id = line
            # Skip empty lines
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            # Next non-empty is broker name
            if j < len(lines):
                broker_name = lines[j].strip()
                j += 1
                # Skip empty lines
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                # Next non-empty is data line
                if j < len(lines):
                    data_line = lines[j].strip()
                    tokens = parse_data_line(data_line)
                    if len(tokens) >= 10:
                        # Map tokens to columns
                        # hold_vol, hold_amt, buy_vol, buy_amt, avg_buy, buy_trans, buy_vol_pct
                        # sell_vol, sell_amt, avg_sell, sell_trans, sell_vol_pct
                        # hb_ratio, matching_vol, matching_amt, matching_trans
                        row = [broker_id, broker_name] + tokens[:16]
                        # Pad if short
                        while len(row) < 18:
                            row.append("0")
                        rows.append(row[:18])
                    i = j + 1
                else:
                    i = j
            else:
                i += 1
        else:
            i += 1
    
    if not rows:
        print(f"WARNING: No rows parsed for {symbol}")
        return False
    
    filepath = f"sharehub_data/{symbol.upper()}_brokers.csv"
    headers = [
        "broker_id", "broker_name",
        "hold_vol", "hold_amt",
        "buy_vol", "buy_amt", "avg_buy", "buy_trans", "buy_vol_pct",
        "sell_vol", "sell_amt", "avg_sell", "sell_trans", "sell_vol_pct",
        "hb_ratio", "matching_vol", "matching_amt", "matching_trans"
    ]
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    
    print(f"OK - Saved {len(rows)} brokers for {symbol} -> {filepath}")
    
    # Show top 5 accumulators
    print(f"\nTop 5 accumulators for {symbol}:")
    sorted_rows = sorted(rows, key=lambda x: float(x[2]) if x[2] else 0, reverse=True)
    for r in sorted_rows[:5]:
        print(f"  Broker {r[0]} ({r[1]}) - Hold: {float(r[2]):,.0f} shares")
    return True

# Test with AKJCL sample
sample = """64


Sun Securities...
22,53,123Rs. 63.84 Cr51,97,305Rs. 1.73 ArabRs. 332.938,3685.4729,44,182Rs. 1.09 ArabRs. 370.884,2633.143.351,33,4694,80,18,915.7182
58


Naasa Securiti...
18,04,274Rs. 40.67 Cr1,18,31,119Rs. 3.89 ArabRs. 329.0321,44512.441,00,26,845Rs. 3.48 ArabRs. 347.6717,97310.5415.2513,04,27145,65,50,066.81,876
60


Nagarik Stock ...
5,28,120Rs. 14.91 Cr20,44,132Rs. 69.83 CrRs. 341.663,2292.1515,16,012Rs. 54.92 CrRs. 362.311,8941.5925.8426,9771,02,26,529.832"""

save_stock_data("AKJCL", sample)
