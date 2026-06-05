@echo off
cd /d "C:\Users\HP User\nepse-quant-terminal"

echo ========================================
echo Testing Option 1 - Full Scan
echo ========================================
python nepse_scanner.py --quickpick
pause

echo ========================================
echo Testing Option 2 - Movers Only
echo ========================================
python nepse_scanner.py --movers-only
pause

echo ========================================
echo Testing Option 3 - Watchlist
echo ========================================
python nepse_scanner.py --watchlist
pause

echo ========================================
echo Testing Option 7 - Sector Trend
echo ========================================
python nepse_scanner.py --sector-trend
pause

echo ========================================
echo Testing Option 7h - Heatmap
echo ========================================
python nepse_scanner.py --heatmap
pause

echo ========================================
echo Testing Option 7r - RS
echo ========================================
python nepse_scanner.py --rs
pause

echo ========================================
echo Testing Option 7w - 52 Week
echo ========================================
python nepse_scanner.py --week52
pause

echo ========================================
echo Testing Option 17b - Broker Holders
echo ========================================
python nepse_scanner.py --broker-holders NABIL
pause

echo ========================================
echo Testing Option 17d - Broker Trend
echo ========================================
python nepse_scanner.py --broker-trend NABIL
pause

echo ========================================
echo Testing Option 17e - Broker Impact
echo ========================================
python nepse_scanner.py --broker-impact
pause

echo ========================================
echo Testing Option 17f - Momentum Hunter
echo ========================================
python nepse_scanner.py --momentum-hunter
pause

echo ========================================
echo Testing Option 18 - Support Resistance
echo ========================================
python nepse_scanner.py --sr NABIL
pause

echo ========================================
echo Testing Option 24 - Portfolio
echo ========================================
python nepse_scanner.py --portfolio
pause

echo ========================================
echo Testing Option 26 - Position Sizer
echo ========================================
python nepse_scanner.py --size NABIL 100000
pause

echo ========================================
echo Testing Option 29 - Value Screen
echo ========================================
python nepse_scanner.py --value
pause

echo ========================================
echo ALL DONE
echo ========================================
pause
