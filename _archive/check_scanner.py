with open('nepse_scanner.py', encoding='utf-8') as f:
    src = f.read()

# Try different menu keywords
for keyword in ['choice', 'Pick', 'menu', 'option', 'launcher', 'def main', 'if __name__']:
    idx = src.find(keyword)
    if idx != -1:
        print(f"--- {keyword} ---")
        print(src[idx:idx+200])
        print()
