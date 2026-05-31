"""
Fix Why engine verdict logic:
  Fix 2: Bull stock + dominant broker SELLING → conflict warning (not "buy pullbacks")
  Fix 3: Bear stock + 60%+ brokers buying → shakeout signal (not "avoid entirely")
  Fix 4: Neutral stock wording — "inline with sector" not "stock-specific weakness"
"""

import shutil, re

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_why_v2.py')
print('Backup saved: nepse_scanner_pre_why_v2.py')

content = open('nepse_scanner.py', encoding='utf-8').read()
lines = content.split('\n')

# ── Step 1: Find the exact verdict blocks ──────────────────────────────
bull_start = None
bear_start = None
neutral_start = None

for i, l in enumerate(lines):
    if "if tag == 'bull':" in l and bull_start is None:
        bull_start = i
    if "if tag == 'bear':" in l and bear_start is None:
        bear_start = i
    if "if tag == 'neutral':" in l and neutral_start is None:
        neutral_start = i

print(f'Bull block:    line {bull_start+1 if bull_start is not None else "NOT FOUND"}')
print(f'Bear block:    line {bear_start+1 if bear_start is not None else "NOT FOUND"}')
print(f'Neutral block: line {neutral_start+1 if neutral_start is not None else "NOT FOUND"}')

# ── Step 2: Fix 2 — Insert conflict check at TOP of bull block ──────────
# We inject: if dominant broker is selling + concentration high/medium → conflict verdict
FIX2_TRIGGER = "if tag == 'bull':"
FIX2_INJECT = """        if tag == 'bull':
            # Conflict: strong RS but dominant broker is net SELLING today
            if da == 'selling' and bstory.get('concentration') in ('high', 'medium') and rs5 > 0:
                verdict = ("Strong RS but dominant broker net SELLING — "
                           "possible distribution at highs. "
                           "Wait for broker to stop selling before entry.")
            el"""

# Replace only first occurrence of the bull block opener
if "if tag == 'bull':\n" in content:
    # Insert the conflict check as first elif by replacing the block start
    old_bull = "        if tag == 'bull':\n            if bstory['history_action'] == 'accumulating'"
    new_bull = """        if tag == 'bull':
            # Conflict: strong RS but dominant broker is net SELLING today
            if da == 'selling' and bstory.get('concentration') in ('high', 'medium') and rs5 > 0:
                verdict = ("Strong RS but dominant broker net SELLING — "
                           "possible distribution at highs. "
                           "Wait for broker to stop selling before entry.")
            elif bstory['history_action'] == 'accumulating'"""
    if old_bull in content:
        content = content.replace(old_bull, new_bull, 1)
        print('Fix 2 applied: bull+selling conflict detection')
    else:
        # Try alternate — find exact lines and patch
        print('Fix 2 alternate: searching for bull block structure...')
        if bull_start is not None:
            # Find the next line after "if tag == 'bull':" which starts the first if
            for j in range(bull_start+1, min(bull_start+5, len(lines))):
                if lines[j].strip().startswith('if ') or lines[j].strip().startswith('elif '):
                    first_if = lines[j]
                    # Build injection before this line
                    indent = '            '
                    injection = [
                        f"{indent}# Conflict: strong RS but dominant broker selling",
                        f"{indent}if da == 'selling' and bstory.get('concentration') in ('high', 'medium') and rs5 > 0:",
                        f"{indent}    verdict = ('Strong RS but dominant broker net SELLING — '",
                        f"{indent}               'possible distribution at highs. '",
                        f"{indent}               'Wait for broker to stop selling before entry.')",
                        f"{indent}el{lines[j].lstrip()}"
                    ]
                    lines[j] = '\n'.join(injection)
                    content = '\n'.join(lines)
                    print(f'  Fix 2 injected before line {j+1}')
                    break
        else:
            print('  Fix 2 FAILED: bull block not found')
else:
    print('Fix 2: bull block opener not found in expected form')

# ── Step 3: Fix 3 — Bear + broad buying = shakeout signal ──────────────
# Find the line: verdict = "Promoter/whale exit while sector rises..."
old_bear_line = '                    verdict = "Promoter/whale exit while sector rises. Stock-specific. Avoid until selling stops."'
new_bear_lines = '''\
                    buy_pct = (bstory.get('buy_brokers', 0) / bstory.get('total_brokers', 1)) * 100
                    if buy_pct > 60:
                        verdict = ("One whale selling while 60%+ brokers buying — "
                                   "possible shakeout before move up. Watch closely.")
                    else:
                        verdict = "Promoter/whale exit while sector rises. Stock-specific. Avoid until selling stops."'''

if old_bear_line in content:
    content = content.replace(old_bear_line, new_bear_lines, 1)
    print('Fix 3 applied: broad buying vs single seller shakeout detection')
else:
    # Search more flexibly
    search = 'Promoter/whale exit while sector rises'
    idx = content.find(search)
    if idx != -1:
        # Find start of that line
        line_start = content.rfind('\n', 0, idx) + 1
        line_end = content.find('\n', idx)
        old_line = content[line_start:line_end]
        indent = len(old_line) - len(old_line.lstrip())
        pad = ' ' * indent
        new_block = (
            f"{pad}buy_pct = (bstory.get('buy_brokers', 0) / bstory.get('total_brokers', 1)) * 100\n"
            f"{pad}if buy_pct > 60:\n"
            f"{pad}    verdict = ('One whale selling while 60%+ brokers buying — '\n"
            f"{pad}               'possible shakeout before move up. Watch closely.')\n"
            f"{pad}else:\n"
            f"{pad}    verdict = 'Promoter/whale exit while sector rises. Stock-specific. Avoid until selling stops.'"
        )
        content = content[:line_start] + new_block + content[line_end:]
        print('Fix 3 applied (flexible match): shakeout detection')
    else:
        print('Fix 3 FAILED: target line not found')

# ── Step 4: Fix neutral "stock-specific weakness" wording ──────────────
# When RS is near 0 (inline), the bullet says "STOCK-SPECIFIC weakness" which is wrong
# Fix: the bullet text is built in get_broker_story or in analyze_why bullet 2
old_neutral_txt = '"STOCK-SPECIFIC weakness, not sector"'
# Actually the issue is in the bullet 2 text for neutral stocks
# Let's find where sec_context is built
sec_ctx_search = 'STOCK-SPECIFIC weakness'
count = content.count(sec_ctx_search)
print(f'Found "STOCK-SPECIFIC weakness" {count} times')

# The bullet 2 for inline stocks should say "inline with sector" not "stock-specific"
# Find the section that builds bullet 2
old_b2 = '— STOCK-SPECIFIC weakness, not sector"'
# This appears when stock underperforms sector — for neutral (rs near 0) we need different text
# Find where sec_context string is assembled
for pattern in [
    'STOCK-SPECIFIC weakness, not sector',
]:
    idx = content.find(pattern)
    while idx != -1:
        line_start = content.rfind('\n', 0, idx) + 1
        line_end = content.find('\n', idx)
        print(f'  Found at: {repr(content[line_start:line_end].strip())}')
        idx = content.find(pattern, idx+1)

# The fix: when rs5 is between -2 and +2, use "inline with sector" wording
# Find where sec_context is set in analyze_why
old_sec_ctx = """    if rs5 >= 0:
        sec_context = f"Sector ({sector}) also rising {sec5:+.1f}% 5D — stock outperforming by {rs5:+.1f}% (momentum confirmed)"
    else:
        sec_context = f"Sector ({sector}) up {sec5:+.1f}% but stock {row['ret5']:+.1f}% — STOCK-SPECIFIC weakness, not sector" """

new_sec_ctx = """    if rs5 >= 2:
        sec_context = f"Sector ({sector}) also rising {sec5:+.1f}% 5D — stock outperforming by {rs5:+.1f}% (momentum confirmed)"
    elif rs5 >= -2:
        sec_context = f"Sector ({sector}) up {sec5:+.1f}% 5D — stock inline with sector ({rs5:+.1f}% RS)"
    else:
        sec_context = f"Sector ({sector}) up {sec5:+.1f}% but stock {row['ret5']:+.1f}% — STOCK-SPECIFIC weakness, not sector" """

if old_sec_ctx in content:
    content = content.replace(old_sec_ctx, new_sec_ctx, 1)
    print('Fix 4 applied: inline sector wording for neutral stocks')
else:
    # Search flexibly
    idx = content.find('STOCK-SPECIFIC weakness, not sector')
    if idx != -1:
        # Find the if/else block around it
        block_search = 'if rs5 >= 0:'
        b_idx = content.rfind(block_search, 0, idx)
        if b_idx != -1:
            b_end = content.find('\n', idx) + 1
            old_block = content[b_idx:b_end]
            # Build replacement
            b_indent = len(old_block.split('\n')[0]) - len(old_block.split('\n')[0].lstrip())
            pad = ' ' * b_indent
            new_block = (
                f"{pad}if rs5 >= 2:\n"
                f"{pad}    sec_context = f\"Sector ({{sector}}) also rising {{sec5:+.1f}}% 5D — stock outperforming by {{rs5:+.1f}}% (momentum confirmed)\"\n"
                f"{pad}elif rs5 >= -2:\n"
                f"{pad}    sec_context = f\"Sector ({{sector}}) up {{sec5:+.1f}}% 5D — stock inline with sector ({{rs5:+.1f}}% RS)\"\n"
                f"{pad}else:\n"
                f"{pad}    sec_context = f\"Sector ({{sector}}) up {{sec5:+.1f}}% but stock {{row['ret5']:+.1f}}% — STOCK-SPECIFIC weakness, not sector\""
            )
            content = content[:b_idx] + new_block + content[b_end:]
            print('Fix 4 applied (flexible): inline sector wording')
        else:
            print('Fix 4 FAILED: if rs5 block not found')
    else:
        print('Fix 4: STOCK-SPECIFIC text not found — may already be patched')

# ── Save ────────────────────────────────────────────────────────────────
open('nepse_scanner.py', 'w', encoding='utf-8').write(content)
print('\nSaved.')

# ── Syntax check ────────────────────────────────────────────────────────
import ast
try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    print('Restoring backup...')
    import shutil
    shutil.copy('nepse_scanner_pre_why_v2.py', 'nepse_scanner.py')
    print('Backup restored. No changes applied.')
