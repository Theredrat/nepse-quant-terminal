lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
# Show lines 8064-8082 with repr to see exact indentation
for i in range(8063, 8082):
    print(i+1, repr(lines[i]))
