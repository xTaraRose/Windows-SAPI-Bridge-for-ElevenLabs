# Windows SAPI Bridge Cleanup Guide

## The Problem

If you moved the Windows SAPI Bridge for ElevenLabs files to a new location or encountered errors during installation, you may experience **high CPU usage** from leftover Windows services trying to start services that no longer exist.

### Symptoms

- **High CPU usage** consistently pegged even after restart
- **SvcHost (No Network)** process consuming significant CPU
- **IAStorDataMgrSvc** and related processes stuck in restart loops
- **Task Manager** showing lingering SAPI Bridge-related services
- Voice registrations **not appearing** in applications despite running install_voices.py again

### Root Cause

When the SAPI Bridge installer (`install_voices.py`) runs, it:
1. Creates voice registrations in `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens`
2. Registers a COM engine object (CLSID) in `HKEY_LOCAL_MACHINE\SOFTWARE\Classes\CLSID`
3. Points these registrations to the Python executable and script files

If the SAPI Bridge files are **moved, deleted, or relocated** without running the proper uninstall script from the original location, the Windows registry still has:
- Pointers to non-existent files
- COM object definitions with broken references
- Voice registrations pointing to removed paths

This causes Windows to repeatedly attempt to initialize these services, resulting in high CPU usage and errors in the Event Viewer.

## The Solution

### Option 1: Standard Uninstall (if you still have the original location)

From the **original** SAPI Bridge directory:

```bash
python uninstall_voices.py
```

This reads the `.installed_voices.json` state file to know exactly what was registered and removes it cleanly.

### Option 2: Emergency Cleanup (recommended if files were moved)

From the **current** SAPI Bridge directory (wherever the files are now):

```bash
python cleanup_sapi_bridge.py
```

This comprehensive cleanup script:
- **Doesn't depend on the state file** — works even if `.installed_voices.json` is missing
- **Scans the registry** for all ElevenLabs registrations
- **Removes all traces** — voices, CLSID, state files, and optionally config
- **Verifies the cleanup** — confirms all registrations are gone
- **Handles edge cases** — works regardless of where files were moved

#### Usage Examples

```bash
# Standard cleanup
python cleanup_sapi_bridge.py

# Preserve your config.json (API key) if you want to reinstall later
python cleanup_sapi_bridge.py --preserve-config

# See detailed output of what's being removed
python cleanup_sapi_bridge.py --verbose

# Both options together
python cleanup_sapi_bridge.py --preserve-config --verbose
```

### Step-by-Step Instructions

1. **Locate the SAPI Bridge directory** wherever you have it now (e.g., `E:\##Development\Windows-SAPI-Bridge-for-ElevenLabs`)

2. **Right-click Command Prompt** → **Run as Administrator**

3. **Navigate to the SAPI Bridge directory:**
   ```bash
   cd E:\##Development\Windows-SAPI-Bridge-for-ElevenLabs
   ```

4. **Run the cleanup:**
   ```bash
   python cleanup_sapi_bridge.py --verbose
   ```

5. **Wait for completion** — the script will show a summary of what was removed and verify the cleanup

6. **Restart your computer** (recommended to ensure all services reset)

7. **Verify the fix:**
   - Open **Task Manager** and check that CPU usage is normal
   - Look for "IAStorDataMgrSvc" or "SvcHost (No Network)" — they should no longer be consuming CPU
   - Check that no errors appear in **Event Viewer** related to ElevenLabs

## After Cleanup

### If you want to reinstall the SAPI Bridge later:

```bash
python install_voices.py
```

This will re-register all voices cleanly with the new location.

### If you're keeping the cleaned-up config.json:

```bash
python install_voices.py --preserve-config
```

This will re-register voices but skip overwriting your existing `config.json`.

## What Gets Removed

The cleanup script removes:

| Item | Location |
|------|----------|
| **Voice Registrations** | `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\ElevenLabs_*` |
| **Engine CLSID** | `HKEY_LOCAL_MACHINE\SOFTWARE\Classes\CLSID\{6C0A3A4E-8F2B-4E5D-A3C7-1B9F2E8D4A6C}` |
| **State File** | `.installed_voices.json` in the SAPI Bridge directory |
| **Config File** | `config.json` (unless `--preserve-config` is used) |

## Why This Happened

This issue commonly occurs because:
1. **Files were moved** after installation without uninstalling first
2. **Repository was cloned/copied** to a new location with existing registrations
3. **System images/backups** were restored with old registry entries pointing to removed paths
4. **Uninstall script failed** to complete due to missing dependencies or interrupted process

## Preventing This in the Future

1. **Always run the uninstall script before moving files:**
   ```bash
   python uninstall_voices.py
   ```

2. **Then move the directory to the new location**

3. **Run the install script again from the new location:**
   ```bash
   python install_voices.py
   ```

4. **If cloning/copying the repository:**
   - Run uninstall in the old location first, OR
   - Delete `.installed_voices.json` before cloning, OR
   - Keep the SAPI Bridge in one permanent location

## Troubleshooting

### The cleanup script is slow to start

This is normal — Windows is loading Python. The actual cleanup typically takes a few seconds.

### "ERROR: Must be run as Administrator"

Right-click **Command Prompt** → **Run as Administrator** before running the script.

### Still seeing high CPU usage after cleanup

1. **Restart the computer** — Windows services may need to reinitialize
2. **Manually check Event Viewer:**
   - Open **Event Viewer** → **Windows Logs** → **System**
   - Look for errors related to "ElevenLabs" or "COM"
   - These should be gone after cleanup + restart

3. **If problems persist:**
   - Run `cleanup_sapi_bridge.py --verbose` again to see what it's removing
   - Check if other SAPI5 installations might be conflicting
   - Consider creating a system restore point and checking Event Viewer errors in detail

### Want to verify the cleanup worked?

Open **Registry Editor** (`regedit`) and check:
1. `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens` — should have no `ElevenLabs_` entries
2. `HKEY_LOCAL_MACHINE\SOFTWARE\Classes\CLSID\{6C0A3A4E-8F2B-4E5D-A3C7-1B9F2E8D4A6C}` — should not exist

## Still Having Issues?

If you still experience problems after cleanup:

1. **Comment on the GitHub issue** with:
   - Output from `python cleanup_sapi_bridge.py --verbose`
   - What you see in **Event Viewer** errors
   - When the issue started (after moving files, cloning repo, etc.)

2. **Check Event Viewer for root cause:**
   - Event Viewer → Windows Logs → System
   - Look for errors containing "ElevenLabs", "COM", "CLSID", or "Service"
   - These logs will show the exact registry path causing issues

This information helps us improve the cleanup utility and prevent similar issues in the future.
