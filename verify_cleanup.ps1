# Verification script to confirm SAPI Bridge cleanup was successful
# Run this AFTER cleanup_sapi_bridge.py and after restarting your computer

Write-Host ""
Write-Host "=== SAPI Bridge Cleanup Verification ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking for SAPI Bridge artifacts..." -ForegroundColor Yellow
Write-Host ""

# Check 1: CLSID should be gone
Write-Host "1. Engine CLSID Check" -ForegroundColor Cyan
$clsidExists = $false
try {
    Get-Item "HKLM:\SOFTWARE\Classes\CLSID\{6C0A3A4E-8F2B-4E5D-A3C7-1B9F2E8D4A6C}" -ErrorAction Stop | Out-Null
    $clsidExists = $true
} catch {}

if($clsidExists) {
    Write-Host "  [FAIL] CLSID still exists (cleanup may have failed)" -ForegroundColor Red
} else {
    Write-Host "  [PASS] CLSID successfully removed" -ForegroundColor Green
}

# Check 2: Voice tokens should be gone
Write-Host ""
Write-Host "2. Voice Registrations Check" -ForegroundColor Cyan
$orphanedVoices = @()
try {
    $orphanedVoices = Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Speech\Voices\Tokens" -ErrorAction SilentlyContinue |
        Where-Object {$_.PSChildName -like "ElevenLabs_"} |
        Select-Object -ExpandProperty PSChildName
} catch {}

if($orphanedVoices.Count -gt 0) {
    Write-Host "  [FAIL] Found $($orphanedVoices.Count) orphaned voice tokens:" -ForegroundColor Red
    $orphanedVoices | ForEach-Object { Write-Host "         - $_" }
} else {
    Write-Host "  [PASS] No orphaned voice tokens found" -ForegroundColor Green
}

# Check 3: CPU usage should be normal
Write-Host ""
Write-Host "3. CPU Usage Check" -ForegroundColor Cyan
$iastor = Get-Process IAStorDataMgrSvc -ErrorAction SilentlyContinue
if($iastor) {
    $ws = [math]::Round($iastor.WorkingSet/1MB, 2)
    $handles = $iastor.Handles
    Write-Host "  IAStorDataMgrSvc Status:" -ForegroundColor Gray
    Write-Host "    Working Set: $ws MB"
    Write-Host "    Handles: $handles"
    Write-Host "    Threads: $($iastor.Threads.Count)"
    Write-Host ""

    # Check if it's reasonable
    if($handles -lt 500 -and $ws -lt 100) {
        Write-Host "  [PASS] Process appears healthy" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Process may still be problematic (check Task Manager)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [FAIL] IAStorDataMgrSvc not found" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "=== Verification Complete ===" -ForegroundColor Cyan
Write-Host ""

if(-not $clsidExists -and $orphanedVoices.Count -eq 0) {
    Write-Host "SUCCESS: System is clean! SAPI Bridge completely removed." -ForegroundColor Green
} else {
    Write-Host "WARNING: Some issues remain. You may need to:" -ForegroundColor Yellow
    Write-Host "  1. Run cleanup_sapi_bridge.py again with administrator privileges"
    Write-Host "  2. Manually remove remaining registry entries"
    Write-Host "  3. Restart the computer"
}

Write-Host ""
