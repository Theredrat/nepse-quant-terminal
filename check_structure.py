src = open("nepse_scanner.py", encoding="utf-8").read()
lines = src.splitlines()

print("=== LAST 50 LINES (main block) ===")
for i, l in enumerate(lines[-50:], len(lines)-50):
    print(f"{i}: {l}")
