src = open("nepse_scanner.py", encoding="utf-8").read()
lines = src.splitlines()
for i, l in enumerate(lines):
    if "preopen" in l.lower():
        print(f"{i}: {l}")
