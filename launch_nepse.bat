@echo off
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
chcp 437 >nul
cd /d "C:\Users\HP User\nepse-quant-terminal"
call .venv\Scripts\activate
python _backup.py >nul 2>&1
:: BACKUP daily_data before sync
python backup_daily_data.py
:: SYNC - pull latest JSON from GitHub
echo Syncing data...
python _sync_data.py
echo.
:: AUTO FULL SCAN - skips on holidays/weekends
echo Checking market status...
python _marketcheck.py
if errorlevel 1 goto SKIPSCAN
echo Running daily full scan...
python nepse_scanner.py --report
:SKIPSCAN
echo Daily scan complete.
echo.

:: ?????? AUTO-REFRESH SECTORS (weekly, silent) ????????????????????????????????????????????????????????????????????????????????????????????????????????????
python auto_refresh_sectors.py
timeout /t 2 >nul
:: ???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

:MENU
cls
echo.
echo  ============================================
echo        NEPSE SCANNER - QUICK LAUNCH
echo  ============================================
echo.
echo   --- DAILY SCAN ---
echo   1.  Full Scan  (Signals + Movers)
echo   2.  Movers Only  (Gainers / Losers)
echo   3.  Watchlist
echo.
echo   --- STOCK PICKS ---
echo   4.  Quick Pick  (signals only)
echo   5.  Smart Pick  (signals + broker + whale)
echo.
echo   --- SMART MONEY ---
echo   6.  Power Sell Alert
echo   7.  Sector Rotation
echo   7t. Sector Trend  (5/10/20d momentum)
echo   7h. Sector Heatmap
echo   7r. Relative Strength  (RS vs sector)
echo   7rw. RS + Why  (RS with full reasoning)
echo   7w. 52-Week High/Low Alerts
echo   7ww. 52W + Why  (52W with full reasoning)
echo   7b. Broker + RS Accumulation
echo   8.  Whale Tracker
echo   9.  Broker Leaderboard
echo.
echo   --- TOP BROKER TRACKERS ---
echo   10. Broker 58  (Top Whale)
echo   13. Track Any Broker
echo.
echo   --- STOCK ANALYSIS ---
echo   17. Floorsheet - Any Stock
echo   17b. Top Broker Holders - Any Stock
echo   17c. Broker Activity - Specific Date
echo   17d. Broker Trend  (7-day smart money)
echo   17e. Broker Impact  (institutional ranking)
echo   17f. Momentum Hunter (early accumulation)
echo   17p. Pre-Open Band    (5%% up/down calculator)
echo   18. Support/Resistance - Any Stock
echo.
echo   --- PORTFOLIO INTELLIGENCE ---
echo   22. Start Telegram Alerts (background)
echo   23. Sector Correlation Heatmap
echo   24. Portfolio Analysis  (all watchlist)
echo   25. Portfolio - Custom Stocks
echo   26. Position Sizer  (volatility-based)
echo.
echo   --- FUNDAMENTAL ANALYSIS ---
rem   27. Fundamental Snapshot  (any stock)
rem   28. Earnings History      (any stock)
echo   29. Value Screen          (undervalued by sector - ALL)
echo   29s. Value Screen         (specific sector)
rem   30. Float / Ownership     (any stock)
rem   31. Unlock Dates          (upcoming lock-in expiry)
echo   34. Update Quarterly Fundamentals  (smart scrape all equity)
echo.
echo   --- SIGNAL TRACKER ---
echo   32. Signal Performance  (accuracy by signal type)
echo   33. Bloomberg TUI  (full terminal dashboard)
echo.
echo   --- REPORTS ---
echo   19. Full Scan + Save Report
echo   20. Power Sell + Save Report
echo.
echo   --- FULL ANALYSIS ---
  echo   35. Full Stock Report  (one-stop buy/sell decision)
  echo   36. Best R/R Scanner   (stocks with good R/R at current price)
  echo   37. Market Phase        (Accumulation / Markup / Distribution / Markdown)
  echo   38. Seasonality          (best and worst months to trade NEPSE)
  echo   39. Nepali Seasonality     (Baisakh-based true Nepali month analysis)
  echo.
  echo   --- HELP ---
echo   21. Signal Legend / Help
  echo   21b. Buy/Sell Decision Guide
echo   0.  Exit
echo.
set /p choice=  Pick a number and press Enter:
if "%choice%"=="1" goto RUN_FULLSCAN
if "%choice%"=="2" goto RUN_MOVERS
if "%choice%"=="3" goto RUN_WATCHLIST
if "%choice%"=="4"  python nepse_scanner.py --quickpick & goto AGAIN
if "%choice%"=="5"  python nepse_scanner.py --smartpick & goto AGAIN
if "%choice%"=="6"  python nepse_scanner.py --powersell & goto AGAIN
if "%choice%"=="7"  python nepse_scanner.py --sector & goto AGAIN
if "%choice%"=="7t" python nepse_scanner.py --sector-trend & goto AGAIN
if "%choice%"=="7h" python nepse_scanner.py --heatmap & goto AGAIN
if "%choice%"=="7r"  python nepse_scanner.py --rs & goto AGAIN
if "%choice%"=="7rw" python nepse_scanner.py --rs --why & goto AGAIN
if "%choice%"=="7w"  python nepse_scanner.py --week52 & goto AGAIN
if "%choice%"=="7ww" python nepse_scanner.py --week52 --why & goto AGAIN
if "%choice%"=="7b" python nepse_scanner.py --broker-rs & goto AGAIN
if "%choice%"=="8"  python nepse_scanner.py --whale & goto AGAIN
if "%choice%"=="9"  python nepse_scanner.py --brokers & goto AGAIN
if "%choice%"=="10" python nepse_scanner.py --broker 58 & goto AGAIN
if "%choice%"=="13" goto CUSTOM_BROKER
if "%choice%"=="17b" goto CUSTOM_HOLDERS
if "%choice%"=="17c" goto CUSTOM_BROKERDATE
if "%choice%"=="17d" goto BROKER_TREND
if "%choice%"=="17e" goto BROKER_IMPAAT
if "%choice%"=="17f" goto MOMENTUM_HUNTER
if "%choice%"=="17p" goto PREOPEN_CALC
if "%choice%"=="17" goto CUSTOM_FLOOR
if "%choice%"=="18" goto CUSTOM_SR
if "%choice%"=="19" python nepse_scanner.py --report & goto AGAIN
if "%choice%"=="20" python nepse_scanner.py --powersell --report & goto AGAIN
if "%choice%"=="21" python nepse_scanner.py --legend & goto AGAIN
if "%choice%"=="21b" python nepse_scanner.py --guide & goto AGAIN
if "%choice%"=="35" goto FULL_REPORT

if "%choice%"=="36" goto BEST_RR
if "%choice%"=="37" goto MARKET_PHASE
if "%choice%"=="38" goto SEASONALITY
if "%choice%"=="39" goto NEPALI_SEASON
if "%choice%"=="22" start python nepse_alerts.py & goto AGAIN
if "%choice%"=="23" python nepse_scanner.py --corr & goto AGAIN
if "%choice%"=="24" python nepse_scanner.py --portfolio & goto AGAIN
if "%choice%"=="25" goto CUSTOM_PORTFOLIO
if "%choice%"=="26" goto CUSTOM_SIZE
if "%choice%"=="27" goto CUSTOM_FUNDAMENTAL
if "%choice%"=="28" goto CUSTOM_EARNINGS
if "%choice%"=="29" python nepse_scanner.py --value & goto AGAIN
if "%choice%"=="29s" goto CUSTOM_VALUE
if "%choice%"=="30" goto CUSTOM_FLOAT
if "%choice%"=="31" python nepse_scanner.py --unlock upcoming & goto AGAIN
if "%choice%"=="32" python signal_tracker.py --report & goto AGAIN
if "%choice%"=="33" python dashboard_tui.py & goto AGAIN
if "%choice%"=="34" goto UPDATE_FUNDAMENTALS
if "%choice%"=="0"  exit
echo  Invalid choice, try again.
pause
goto MENU

:CUSTOM_BROKER
set /p broker=  Enter broker ID (e.g. 34):
python nepse_scanner.py --broker %broker%
goto AGAIN

:CUSTOM_DATE
set /p dt_sym=  Enter stock symbol (e.g. CHCL):
python nepse_scanner.py --broker-date %dt_sym% prompt
goto AGAIN

:CUSTOM_HOLDERS
set /p symbol=  Enter stock symbol (e.g. BUNGAL):
python nepse_scanner.py --broker-holders %symbol%
goto AGAIN

:CUSTOM_BROKERDATE
set /p symbol=  Enter stock symbol (e.g. CHCL):
python nepse_scanner.py --broker-date %symbol% prompt
goto AGAIN

:BROKER_TREND
set /p btsym=  Enter stock symbol (e.g. JBBL):
python nepse_scanner.py --broker-trend %btsym%
goto AGAIN

:BROKER_IMPAAT
python nepse_scanner.py --broker-impact
goto AGAIN

:MOMENTUM_HUNTER
python nepse_scanner.py --momentum-hunter
goto AGAIN

:PREOPEN_CALC
set /p symbols=  Enter symbol(s) separated by space (e.g. AKJCL GUFL HPPL):
python nepse_scanner.py --preopen %symbols%
goto AGAIN

:CUSTOM_FLOOR
set /p symbol=  Enter stock symbol (e.g. NABIL):
python nepse_scanner.py --floor %symbol%
goto AGAIN

:CUSTOM_SR
set /p symbol=  Enter stock symbol for S/R (e.g. NABIL):
python nepse_scanner.py --sr %symbol%
goto AGAIN

:CUSTOM_PORTFOLIO
set /p symbols=  Enter symbols separated by spaces (e.g. AKJCL BUNGAL BHCL):
python nepse_scanner.py --portfolio %symbols%
goto AGAIN

:CUSTOM_SIZE
set /p symbol=  Enter stock symbol (e.g. AKJCL):
set /p amount=  Enter capital in Rs (e.g. 100000):
python nepse_scanner.py --size %symbol% %amount%
goto AGAIN

:CUSTOM_FUNDAMENTAL
set /p symbol=  Enter stock symbol (e.g. NABIL):
python nepse_scanner.py --fundamental %symbol%
goto AGAIN

:CUSTOM_EARNINGS
set /p symbol=  Enter stock symbol (e.g. AKJCL):
python nepse_scanner.py --earnings %symbol%
goto AGAIN

:CUSTOM_VALUE
echo.
echo   1.  Hydropower
echo   2.  Commercial Bank
echo   3.  Development Bank
echo   4.  Finance
echo   5.  Hotel ^& Tourism
echo   6.  Investment
echo   7.  Life Insurance
echo   8.  Manufacturing and Processing
echo   9.  Microfinance
echo   10. Non-Life Insurance
echo   11. Others
echo   12. Trading
echo.
set /p secnum=  Enter number:
if "%secnum%"=="1"  set sector=Hydropower
if "%secnum%"=="2"  set sector=Commercial Bank
if "%secnum%"=="3"  set sector=Development Bank
if "%secnum%"=="4"  set sector=Finance
if "%secnum%"=="5"  set sector=Hotel ^& Tourism
if "%secnum%"=="6"  set sector=Investment
if "%secnum%"=="7"  set sector=Life Insurance
if "%secnum%"=="8"  set sector=Manufacturing and Processing
if "%secnum%"=="9"  set sector=Microfinance
if "%secnum%"=="10" set sector=Non-Life Insurance
if "%secnum%"=="11" set sector=Others
if "%secnum%"=="12" set sector=Trading
python nepse_scanner.py --value "%sector%"
goto AGAIN

:CUSTOM_FLOAT
set /p symbol=  Enter stock symbol (e.g. NABIL):
python nepse_scanner.py --float %symbol%
goto AGAIN

:RUN_FULLSCAN
python _marketcheck.py
if errorlevel 1 python nepse_scanner.py --offline & goto AGAIN
python nepse_scanner.py
goto AGAIN

:RUN_MOVERS
python _marketcheck.py
if errorlevel 1 python nepse_scanner.py --offline --movers-only & goto AGAIN
python nepse_scanner.py --movers-only
goto AGAIN

:RUN_WATCHLIST
python _marketcheck.py
if errorlevel 1 python nepse_scanner.py --offline --watchlist & goto AGAIN
python nepse_scanner.py --watchlist
goto AGAIN

:UPDATE_FUNDAMENTALS
echo Running smart quarterly scraper...
python backend\quant_pro\smart_scraper.py
goto AGAIN

:FULL_REPORT
set /p symbol=  Enter stock symbol (e.g. NABIL):
python nepse_scanner.py --full-report %symbol%
goto AGAIN

:BEST_RR
python nepse_scanner.py --best-rr
goto AGAIN

:MARKET_PHASE
python nepse_scanner.py --market-phase
goto AGAIN

:NEPALI_SEASON
python nepse_scanner.py --nepali-season
goto AGAIN

:SEASONALITY
python nepse_scanner.py --seasonality
goto AGAIN

:AGAIN
echo.
echo  ============================================
pause
goto MENU

