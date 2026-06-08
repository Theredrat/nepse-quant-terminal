# setup_scheduler.ps1
# Run once as Administrator to register the 4 PM auto-scan task
# Usage: Right-click -> Run with PowerShell (as Admin)

$ProjectDir = "C:\Users\HP User\nepse-quant-terminal"
$PythonExe  = (Get-Command python).Source
$Script     = Join-Path $ProjectDir "auto_daily.py"
$LogDir     = Join-Path $ProjectDir "logs"
$TaskName   = "NEPSE_AutoDaily"

# Create logs folder if missing
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Build the action
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$Script`"" `
    -WorkingDirectory $ProjectDir

# Trigger: every day at 4:00 PM
# NEPSE trades Sun-Thu — the script itself skips Fri/Sat
$Trigger = New-ScheduledTaskTrigger -Daily -At "4:00PM"

# Settings
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -RunOnlyIfNetworkAvailable

# Principal — run as current user
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# Register (replace if exists)
$Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed existing task: $TaskName"
}

Register-ScheduledTask `
    -TaskName  $TaskName `
    -Action    $Action `
    -Trigger   $Trigger `
    -Settings  $Settings `
    -Principal $Principal `
    -Description "NEPSE auto scan: sync + quickpick + smartpick + momentum hunter + signal tracker update at 4PM daily"

Write-Host ""
Write-Host "Task registered successfully: $TaskName"
Write-Host "Runs every day at 4:00 PM"
Write-Host "NEPSE trading days (Sun-Thu) will run full scan"
Write-Host "Friday/Saturday will be skipped automatically"
Write-Host ""
Write-Host "To verify: Open Task Scheduler -> Task Scheduler Library -> NEPSE_AutoDaily"
Write-Host "To test now: python `"$Script`""
Write-Host "To view log: Get-Content `"$LogDir\auto_daily.log`" -Tail 30"
