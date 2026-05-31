content = open('nepse_scanner.py', encoding='utf-8').read()

old = "    need_floor = any([args.floor, args.brokers, args.powersell, args.sector, args.whale, args.sr, args.broker, args.smartpick])"
new = "    need_floor = any([args.floor, args.brokers, args.powersell, args.sector, args.whale, args.sr, args.broker, args.smartpick, getattr(args, 'why', False)])"

if old in content:
    content = content.replace(old, new)
    open('nepse_scanner.py', 'w', encoding='utf-8').write(content)
    print('Fixed: --why now fetches floorsheet automatically')
else:
    print('ERROR: line not found')
