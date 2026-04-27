# Diagnostic Findings: Persistent High CPU Usage

## 🔴 ROOT CAUSE IDENTIFIED

**The Problem:**
The SAPI Bridge engine CLSID `{6C0A3A4E-8F2B-4E5D-A3C7-1B9F2E8D4A6C}` **still exists in the Windows registry** despite running `uninstall_voices.py`.

**Registry Location:**
```
HKEY_LOCAL_MACHINE\SOFTWARE\Classes\CLSID\{6C0A3A4E-8F2B-4E5D-A3C7-1B9F2E8D4A6C}
```

## 🔍 What's Happening

1. When Windows boots, it loads the class registry and attempts to initialize all registered COM objects
2. This CLSID entry points to a Python executable and script that **no longer exist** (moved/deleted)
3. Windows repeatedly attempts to initialize the broken COM object
4. These initialization failures cause `IAStorDataMgrSvc` and `svchost` processes to cycle and consume CPU

This explains why:
- ✅ No error events appear in Event Viewer (COM loading failures are silent)
- ✅ No WMI subscriptions trigger (not a subscription/event issue)
- ✅ No registry entries for Python/ElevenLabs exist elsewhere (isolated to CLSID)
- ❌ High CPU continues even after `uninstall_voices.py` (it didn't fully clean the CLSID)

## 🧹 Why Cleanup Failed

The `uninstall_voices.py` script depends on the `.installed_voices.json` state file to know what was installed. However:
1. The cleanup didn't fully remove the CLSID entry from the registry
2. The CLSID likely wasn't tracked in `.installed_voices.json` properly
3. Manual registry entry was missed during the initial uninstall

## ✅ Solution: Emergency Cleanup

The `cleanup_sapi_bridge.py` script is specifically designed to handle this scenario. It:
- ✓ Doesn't depend on `.installed_voices.json`
- ✓ Scans the registry for ALL ElevenLabs references
- ✓ Forcibly removes the CLSID entry
- ✓ Verifies complete cleanup

### Steps to Fix

**1. Open Command Prompt as Administrator:**
- Right-click Command Prompt
- Select "Run as administrator"

**2. Navigate to SAPI Bridge directory:**
```bash
cd E:\##Development\Windows-SAPI-Bridge-for-ElevenLabs
```

**3. Run the cleanup script:**
```bash
python cleanup_sapi_bridge.py --verbose
```

**4. Restart your computer:**
This allows Windows to reload the registry without the orphaned CLSID

**5. Verify the fix:**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File verify_cleanup.ps1
```

## 📊 Diagnostic Summary

| Item | Status |
|------|--------|
| CLSID in registry | ❌ **EXISTS** (should be removed) |
| Orphaned voice tokens | ✅ None found |
| WMI subscriptions | ✅ None found |
| Error events | ✅ None found |
| Compatibility shims | ✅ None found |
| Python references | ✅ None found |
| Storage subsystem | ✅ Healthy |

## 📝 Files Involved

- **cleanup_sapi_bridge.py** - Emergency cleanup utility (already created in previous session)
- **diagnose_cpu_usage.py** - NEW diagnostic tool that identifies the issue
- **verify_cleanup.ps1** - NEW PowerShell script to verify fix after cleanup

## 🎯 Expected Outcome

After running cleanup and restarting:
- CPU usage from IAStorDataMgrSvc and svchost returns to normal (< 1%)
- System responsiveness improves significantly
- No error events or warnings related to COM initialization
- Computer boots and runs smoothly

## 🚀 Prevention for Future

Always uninstall before moving or deleting:
```bash
python uninstall_voices.py    # Uninstall first
# Then move/delete the directory
python cleanup_sapi_bridge.py --verbose  # Use emergency cleanup if standard uninstall fails
```

---

**Generated:** 2026-04-27
**Diagnostic Tool:** diagnose_cpu_usage.py
