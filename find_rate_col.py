with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find get_floorsheet_of_symbol to see what columns it returns
import re
matches = [(m.start(), m.group()) for m in re.finditer(r'def get_floorsheet_of_symbol', content)]
for pos, _ in matches:
    print(content[pos:pos+300])
    print()

# Also find where floorsheet columns are defined/renamed
for term in ["'rate'", '"rate"', "contractRate", "tradeRate", "rename"]:
    idxs = [i for i in range(len(content)) if content[i:i+len(term)] == term]
    if idxs:
        print(f"'{term}' found at {len(idxs)} locations, first: ...{content[max(0,idxs[0]-50):idxs[0]+50]}...")
        print()
