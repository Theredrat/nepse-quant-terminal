from nepse import Nepse
n = Nepse()
n.setTLSVerification(False)
import inspect
members = inspect.getmembers(n, predicate=inspect.ismethod)
for name,_ in members: print(name)
print(chr(45)*30)
print(chr(65)+chr(80)+chr(73)+chr(32)+chr(101)+chr(110)+chr(100)+chr(112)+chr(111)+chr(105)+chr(110)+chr(116)+chr(115)+chr(58))
for k in n.api_end_points: print(k)
