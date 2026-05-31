from nepse import Nepse
n = Nepse()
n.setTLSVerification(False)
methods = [m for m in dir(n) if not m.startswith(chr(95))]
for m in methods: print(m)
