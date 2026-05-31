import ast

code = open("nepse_alerts_ci.py", encoding="utf-8").read()

# Check if already updated
if "morning_briefing" in code:
    print("Already updated")
else:
    print("Needs update - downloading from template")
    # Write marker so we know to update
    open("needs_ci_update.txt", "w").write("yes")
    print("Created needs_ci_update.txt")
