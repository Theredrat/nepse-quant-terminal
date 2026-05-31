def analyze_watchlist(live_df):
    import json, sqlite3 as _sq
    from pathlib import Path
    console.print()
    console.print(Rule(chr(91)+chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93)+chr(83)+chr(109)+chr(97)+chr(114)+chr(116)+chr(32)+chr(87)+chr(97)+chr(116)+chr(99)+chr(104)+chr(108)+chr(105)+chr(115)+chr(116)+chr(91)+chr(47)+chr(98)+chr(111)+chr(108)+chr(100)+chr(93), style=chr(103)+chr(114)+chr(101)+chr(101)+chr(110)))
    console.print()
    if live_df is None or live_df.empty:
        console.print(chr(91)+chr(114)+chr(101)+chr(100)+chr(93)+chr(78)+chr(111)+chr(32)+chr(108)+chr(105)+chr(118)+chr(101)+chr(32)+chr(100)+chr(97)+chr(116)+chr(97)+chr(46)+chr(91)+chr(47)+chr(114)+chr(101)+chr(100)+chr(93))
        return
    WL_PATH=Path(chr(100)+chr(97)+chr(116)+chr(97)+chr(47)+chr(114)+chr(117)+chr(110)+chr(116)+chr(105)+chr(109)+chr(101)+chr(47)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(115)+chr(47)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(95)+chr(49)+chr(47)+chr(119)+chr(97)+chr(116)+chr(99)+chr(104)+chr(108)+chr(105)+chr(115)+chr(116)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110))
    wl_syms=WATCHLIST
    wl_scores={s:0 for s in wl_syms}
    if WL_PATH.exists():
        try:
            wl_data=json.load(open(WL_PATH,encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)))
            wl_syms=[e[chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)] for e in wl_data if e.get(chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108))]
            wl_scores={e[chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)]:e.get(chr(115)+chr(99)+chr(111)+chr(114)+chr(101),0) for e in wl_data if e.get(chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108))}
        except: pass
    if not wl_syms:
        console.print(chr(91)+chr(121)+chr(101)+chr(108)+chr(108)+chr(111)+chr(119)+chr(93)+chr(78)+chr(111)+chr(32)+chr(115)+chr(116)+chr(111)+chr(99)+chr(107)+chr(115)+chr(32)+chr(121)+chr(101)+chr(116)+chr(46)+chr(32)+chr(82)+chr(117)+chr(110)+chr(32)+chr(102)+chr(117)+chr(108)+chr(108)+chr(32)+chr(115)+chr(99)+chr(97)+chr(110)+chr(32)+chr(102)+chr(105)+chr(114)+chr(115)+chr(116)+chr(46)+chr(91)+chr(47)+chr(121)+chr(101)+chr(108)+chr(108)+chr(111)+chr(119)+chr(93))
        return
    t=Table(title=chr(83)+chr(109)+chr(97)+chr(114)+chr(116)+chr(32)+chr(87)+chr(97)+chr(116)+chr(99)+chr(104)+chr(108)+chr(105)+chr(115)+chr(116)+chr(32)+chr(45)+chr(32)+chr(84)+chr(111)+chr(112)+chr(32)+chr(80)+chr(105)+chr(99)+chr(107)+chr(115)+chr(32)+chr(98)+chr(121)+chr(32)+chr(83)+chr(99)+chr(111)+chr(114)+chr(101),box=box.ROUNDED,border_style=chr(103)+chr(114)+chr(101)+chr(101)+chr(110),header_style=chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110))
    t.add_column(chr(35),width=4,style=chr(100)+chr(105)+chr(109))
    t.add_column(chr(83)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108),width=10,style=chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(119)+chr(104)+chr(105)+chr(116)+chr(101))
    t.add_column(chr(83)+chr(99)+chr(111)+chr(114)+chr(101),width=7,justify=chr(114)+chr(105)+chr(103)+chr(104)+chr(116),style=chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(99)+chr(121)+chr(97)+chr(110))
    t.add_column(chr(76)+chr(84)+chr(80),width=12,justify=chr(114)+chr(105)+chr(103)+chr(104)+chr(116))
    t.add_column(chr(67)+chr(104)+chr(103)+chr(37),width=9,justify=chr(114)+chr(105)+chr(103)+chr(104)+chr(116))
    t.add_column(chr(86)+chr(111)+chr(108)+chr(117)+chr(109)+chr(101),width=10,justify=chr(114)+chr(105)+chr(103)+chr(104)+chr(116))
    t.add_column(chr(84)+chr(117)+chr(114)+chr(110)+chr(111)+chr(118)+chr(101)+chr(114),width=14,style=chr(121)+chr(101)+chr(108)+chr(108)+chr(111)+chr(119))
    t.add_column(chr(83)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115),width=28)
    _conn2=_sq.connect(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(95)+chr(100)+chr(97)+chr(116)+chr(97)+chr(46)+chr(100)+chr(98))
    _w52={}
    for _sym in wl_syms:
        try:
            _cur=_conn2.execute(chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(77)+chr(65)+chr(88)+chr(40)+chr(104)+chr(105)+chr(103)+chr(104)+chr(41)+chr(44)+chr(77)+chr(73)+chr(78)+chr(40)+chr(108)+chr(111)+chr(119)+chr(41)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(115)+chr(116)+chr(111)+chr(99)+chr(107)+chr(95)+chr(112)+chr(114)+chr(105)+chr(99)+chr(101)+chr(115)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)+chr(61)+chr(63)+chr(32)+chr(65)+chr(78)+chr(68)+chr(32)+chr(100)+chr(97)+chr(116)+chr(101)+chr(62)+chr(61)+chr(100)+chr(97)+chr(116)+chr(101)+chr(40)+chr(39)+chr(110)+chr(111)+chr(119)+chr(39)+chr(44)+chr(39)+chr(45)+chr(51)+chr(54)+chr(53)+chr(32)+chr(100)+chr(97)+chr(121)+chr(115)+chr(39)+chr(41),(_sym,))
            _row=_cur.fetchone()
            _w52[_sym]={chr(104)+chr(105)+chr(103)+chr(104):_row[0] or 0,chr(108)+chr(111)+chr(119):_row[1] or 0}
        except: _w52[_sym]={chr(104)+chr(105)+chr(103)+chr(104):0,chr(108)+chr(111)+chr(119):0}
    _conn2.close()
    sorted_syms=sorted(wl_syms,key=lambda s:wl_scores.get(s,0),reverse=True)
    for rank,sym in enumerate(sorted_syms,1):
        row=live_df[live_df[chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)].str.upper()==sym.upper()]
        if row.empty:
            t.add_row(str(rank),sym,chr(45),chr(78)+chr(47)+chr(65),chr(78)+chr(47)+chr(65),chr(78)+chr(47)+chr(65),chr(78)+chr(47)+chr(65),chr(91)+chr(100)+chr(105)+chr(109)+chr(93)+chr(78)+chr(111)+chr(116)+chr(32)+chr(116)+chr(114)+chr(97)+chr(100)+chr(105)+chr(110)+chr(103)+chr(91)+chr(47)+chr(100)+chr(105)+chr(109)+chr(93))
            continue
        r=row.iloc[0]
        ltp=r.get(chr(108)+chr(116)+chr(112),0)
        chg=r.get(chr(99)+chr(104)+chr(97)+chr(110)+chr(103)+chr(101)+chr(95)+chr(112)+chr(99)+chr(116),0)
        high52=_w52.get(sym,{}).get(chr(104)+chr(105)+chr(103)+chr(104),0)
        low52=_w52.get(sym,{}).get(chr(108)+chr(111)+chr(119),0)
        score=wl_scores.get(sym,0)
        parts=[]
        if pd.notna(high52) and high52>0 and pd.notna(ltp):
            dist_high=(high52-ltp)/high52*100
            dist_low=(ltp-low52)/low52*100 if pd.notna(low52) and low52>0 else 100
            if dist_high<=3: parts.append(chr(91)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93)+chr(66)+chr(82)+chr(69)+chr(65)+chr(75)+chr(79)+chr(85)+chr(84)+chr(91)+chr(47)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93))
            elif dist_low<=5 and chg>0: parts.append(chr(91)+chr(99)+chr(121)+chr(97)+chr(110)+chr(93)+chr(66)+chr(79)+chr(85)+chr(78)+chr(67)+chr(69)+chr(91)+chr(47)+chr(99)+chr(121)+chr(97)+chr(110)+chr(93))
            elif chg>=5: parts.append(chr(91)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93)+chr(83)+chr(84)+chr(82)+chr(79)+chr(78)+chr(71)+chr(91)+chr(47)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93))
            elif chg<=-3: parts.append(chr(91)+chr(114)+chr(101)+chr(100)+chr(93)+chr(68)+chr(82)+chr(79)+chr(80)+chr(80)+chr(73)+chr(78)+chr(71)+chr(91)+chr(47)+chr(114)+chr(101)+chr(100)+chr(93))
        status=chr(32).join(parts) if parts else chr(91)+chr(100)+chr(105)+chr(109)+chr(93)+chr(78)+chr(111)+chr(114)+chr(109)+chr(97)+chr(108)+chr(91)+chr(47)+chr(100)+chr(105)+chr(109)+chr(93)
        score_str=(chr(91)+chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(99)+chr(121)+chr(97)+chr(110)+chr(93)+str(score)+chr(91)+chr(47)+chr(98)+chr(111)+chr(108)+chr(100)+chr(93)) if score>0 else chr(45)
        ltp_str=(chr(82)+chr(115)+chr(32)+str(round(ltp,2))) if pd.notna(ltp) else chr(78)+chr(47)+chr(65)
        t.add_row(str(rank),sym,score_str,ltp_str,color_change(chg),fmt_vol(r.get(chr(118)+chr(111)+chr(108)+chr(117)+chr(109)+chr(101),0)),fmt_rs(r.get(chr(116)+chr(117)+chr(114)+chr(110)+chr(111)+chr(118)+chr(101)+chr(114),0)),status)
    console.print(t)
    console.print(chr(91)+chr(100)+chr(105)+chr(109)+chr(93)+chr(65)+chr(117)+chr(116)+chr(111)+chr(45)+chr(117)+chr(112)+chr(100)+chr(97)+chr(116)+chr(101)+chr(100)+chr(32)+chr(100)+chr(97)+chr(105)+chr(108)+chr(121)+chr(32)+chr(98)+chr(121)+chr(32)+chr(82)+chr(83)+chr(43)+chr(66)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(43)+chr(86)+chr(111)+chr(108)+chr(117)+chr(109)+chr(101)+chr(32)+chr(115)+chr(99)+chr(111)+chr(114)+chr(105)+chr(110)+chr(103)+chr(91)+chr(47)+chr(100)+chr(105)+chr(109)+chr(93))