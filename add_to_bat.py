src = open("launch_nepse.bat", encoding="utf-8").read()

# Add to menu display - under STOCK ANALYSIS section
old_menu = "   17f. Momentum Hunter (early accumulation)"
new_menu = """   17f. Momentum Hunter (early accumulation)
echo   17p. Pre-Open Band    (5%% up/down calculator)"""
src = src.replace(old_menu, new_menu)

# Add choice handler - after 17f handler
old_choice = 'if "%choice%"=="17f" goto MOMENTUM_HUNTER'
new_choice = '''if "%choice%"=="17f" goto MOMENTUM_HUNTER
if "%choice%"=="17p" goto PREOPEN_CALC'''
src = src.replace(old_choice, new_choice)

# Add the label - after :MOMENTUM_HUNTER block
old_label = ":CUSTOM_FLOOR"
new_label = """:PREOPEN_CALC
set /p symbols=  Enter symbol(s) separated by space (e.g. AKJCL GUFL HPPL):
python nepse_scanner.py --preopen %symbols%
goto AGAIN

:CUSTOM_FLOOR"""
src = src.replace(old_label, new_label)

open("launch_nepse.bat", "w", encoding="utf-8").write(src)
print("Done")
