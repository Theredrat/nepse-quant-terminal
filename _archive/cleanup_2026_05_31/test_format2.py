# Read the actual pasted data from a file instead
# First create a test file with the raw data
raw = open("sharehub_data/AKJCL_raw.txt", encoding="utf-8").read()
lines = raw.splitlines()
for i, line in enumerate(lines[:20]):
    print(f"{i:3} | repr: {repr(line)}")
