src = open("_marketcheck.py", encoding="utf-8").read()
lines = src.splitlines()
for i, l in enumerate(lines):
    if "2026" in l or "closed" in l.lower() or "datetime" in l.lower() or "now" in l.lower():
        print(f"{i}: {l}")
