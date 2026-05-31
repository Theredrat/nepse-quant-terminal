"""
NEPSE Function Checker
Run this after any change to verify nothing is broken.
Usage: python test_all_functions.py
"""

import subprocess, sys, os

env = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'}

# Functions testable without live market data
offline_tests = [
    ['--quickpick'],
    ['--sector-trend'],
    ['--heatmap'],
    ['--rs'],
    ['--rs', '--why'],
    ['--week52'],
    ['--week52', '--why'],
    ['--watchlist'],
    ['--movers-only'],
    ['--corr'],
    ['--legend'],
    ['--momentum-hunter'],
    ['--broker-impact'],
    ['--value'],
    ['--report'],
    ['--unlock', 'upcoming'],
    ['--fundamental', 'AKJCL'],
    ['--earnings', 'AKJCL'],
    ['--float', 'AKJCL'],
    ['--broker-holders', 'AKJCL'],
    ['--broker-trend', 'AKJCL'],
    ['--size', 'AKJCL', '100000'],
    ['--portfolio'],
]

# Functions that only work during market hours (live API needed)
live_only = [
    '--smartpick',
    '--powersell',
    '--sector',
    '--broker-rs',
    '--whale',
    '--brokers',
    '--broker 58',
    '--floor AKJCL',
    '--sr AKJCL',
    '--rs --why',
    '--week52 --why',
]

print()
print('=' * 55)
print('  NEPSE Function Test')
print('=' * 55)

ok_count = 0
fail_count = 0
results = []

for args in offline_tests:
    flag = ' '.join(args)
    print(f'  Testing {flag}...', end='', flush=True)
    try:
        r = subprocess.run(
            [sys.executable, 'nepse_scanner.py'] + args,
            capture_output=True, encoding='utf-8', errors='replace',
            timeout=90, env=env
        )
        ok = r.returncode == 0 and 'Traceback' not in r.stdout and 'Traceback' not in r.stderr
        if ok:
            print(' OK')
            ok_count += 1
            results.append((flag, 'OK', ''))
        else:
            lines = (r.stdout + r.stderr).splitlines()
            err = next((l for l in lines if 'Error' in l or 'Traceback' in l), '')[:50]
            print(f' FAIL')
            print(f'    -> {err}')
            fail_count += 1
            results.append((flag, 'FAIL', err))
    except subprocess.TimeoutExpired:
        print(' TIMEOUT (>45s)')
        fail_count += 1
        results.append((flag, 'TIMEOUT', ''))
    except Exception as e:
        print(f' ERROR: {e}')
        fail_count += 1
        results.append((flag, 'ERROR', str(e)))

print()
print('=' * 55)
print(f'  RESULT: {ok_count} passed, {fail_count} failed out of {len(offline_tests)} tests')
print('=' * 55)

if fail_count > 0:
    print()
    print('  FAILED:')
    for flag, status, err in results:
        if status != 'OK':
            print(f'    - {flag}: {status}')
            if err:
                print(f'      {err}')

print()
print('  NOTE - these need live market hours (not tested here):')
for f in live_only:
    print(f'    - {f}')
print()
