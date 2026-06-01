src = open("nepse_scanner.py", encoding="utf-8").read()
lines = src.splitlines()

# Find cmd_preopen and show the table search loop
for i, l in enumerate(lines):
    if "def cmd_preopen" in l:
        print(f"Found at line {i}")
        for j in range(i, i+40):
            print(f"{j}: {lines[j]}")
        break
