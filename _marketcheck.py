from nepse import Nepse
import sys
try:
    n = Nepse()
    n.setTLSVerification(False)
    status = n.getMarketStatus()
    is_open = status.get(chr(105)+chr(115)+chr(79)+chr(112)+chr(101)+chr(110),chr(67)+chr(76)+chr(79)+chr(83)+chr(69))
    as_of = status.get(chr(97)+chr(115)+chr(79)+chr(102),chr(63))
    if is_open == chr(79)+chr(80)+chr(69)+chr(78):
        print(chr(77)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(32)+chr(105)+chr(115)+chr(32)+chr(79)+chr(80)+chr(69)+chr(78)+chr(32)+chr(45)+chr(32)+chr(114)+chr(117)+chr(110)+chr(110)+chr(105)+chr(110)+chr(103)+chr(32)+chr(115)+chr(99)+chr(97)+chr(110)+chr(46)+chr(46)+chr(46))
        sys.exit(0)
    else:
        print(chr(77)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(32)+chr(105)+chr(115)+chr(32)+chr(67)+chr(76)+chr(79)+chr(83)+chr(69)+chr(68)+chr(32)+chr(40)+as_of+chr(41)+chr(32)+chr(45)+chr(32)+chr(115)+chr(107)+chr(105)+chr(112)+chr(112)+chr(105)+chr(110)+chr(103)+chr(32)+chr(115)+chr(99)+chr(97)+chr(110))
        sys.exit(1)
except Exception as e:
    print(chr(67)+chr(97)+chr(110)+chr(110)+chr(111)+chr(116)+chr(32)+chr(99)+chr(104)+chr(101)+chr(99)+chr(107)+chr(32)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(32)+chr(115)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115)+chr(58),str(e))
    sys.exit(1)
