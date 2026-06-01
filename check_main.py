src = open("nepse_scanner.py", encoding="utf-8").read()
lines = src.splitlines()

# Find main() function
for i, l in enumerate(lines):
    if "def main" in l:
        print(f"main() starts at line {i}")
        for j in range(i, min(i+80, len(lines))):
            print(f"{j}: {lines[j]}")
        break
