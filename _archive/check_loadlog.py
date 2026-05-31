with open('signal_tracker.py', encoding='utf-8') as f:
    src = f.read()
idx = src.find('def load_log')
print(repr(src[idx:idx+120]))
