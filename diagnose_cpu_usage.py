"""
Windows SAPI Bridge for ElevenLabs — CPU Usage Diagnostic Tool
================================================================
Detailed diagnostic utility to identify why IAStorDataMgrSvc and svchost
continue consuming high CPU even after SAPI Bridge cleanup.

This script analyzes:
- Process thread activity and CPU time
- Open file/registry handles
- Service dependencies and state
- WMI configuration
- Event log errors
- Registry integrity

MUST be run as Administrator.
Usage:  python diagnose_cpu_usage.py
"""

import sys
import os
import json
import ctypes
import subprocess
import time
import io
from datetime import datetime

# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import winreg
except ImportError as e:
    print(f'ERROR: Missing required module: {e}')
    sys.exit(1)


# ─── Constants ────────────────────────────────────────────────────────────────

TARGET_PROCESSES = ['IAStorDataMgrSvc', 'svchost']
ENGINE_CLSID = '{6C0A3A4E-8F2B-4E5D-A3C7-1B9F2E8D4A6C}'
REPORT_FILE = os.path.join(os.path.dirname(__file__), 'cpu_diagnostic_report.json')


# ─── Helper Functions ─────────────────────────────────────────────────────────

def banner(title: str, char: str = '═'):
    """Print a formatted banner."""
    width = len(title) + 4
    print(f'\n╔{char * (width - 2)}╗')
    print(f'║  {title}  ║')
    print(f'╚{char * (width - 2)}╝\n')


def check_admin():
    """Verify the script is running as Administrator."""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print('ERROR: This script must be run as Administrator.')
        sys.exit(1)


def run_powershell(command: str) -> str:
    """Execute a PowerShell command and return output."""
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', command],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def get_process_details() -> dict:
    """Collect detailed information about target processes."""
    details = {}

    print('Collecting process details...')

    # Get process list
    cmd = '''
    $procs = @{}
    foreach($name in @('IAStorDataMgrSvc', 'svchost')) {
        $p = Get-Process $name -ErrorAction SilentlyContinue | Select-Object -First 1
        if($p) {
            $procs[$name] = @{
                PID = $p.Id
                WorkingSet = $p.WorkingSet
                Handles = $p.Handles
                Threads = $p.Threads.Count
                StartTime = $p.StartTime
                UserProcessorTime = $p.UserProcessorTime.TotalSeconds
                PrivilegedProcessorTime = $p.PrivilegedProcessorTime.TotalSeconds
            }
        }
    }
    $procs | ConvertTo-Json -Depth 10
    '''

    output = run_powershell(cmd)
    try:
        details['processes'] = json.loads(output)
        print(f"  ✓ Found {len(details['processes'])} target processes")
    except:
        print(f"  ✗ Could not parse process data: {output[:100]}")
        details['processes'] = {}

    return details


def get_service_status() -> dict:
    """Check service configuration and state."""
    status = {}

    print('Checking service status...')

    services = ['IAStorDataMgrSvc', 'PcaSvc', 'Winmgmt']

    cmd = f'''
    $svcStatus = @{{}}
    @({', '.join([f'"{svc}"' for svc in services])}) | ForEach-Object {{
        $svc = $_
        $s = Get-Service $svc -ErrorAction SilentlyContinue
        if($s) {{
            $regPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\$svc"
            $props = Get-ItemProperty $regPath -ErrorAction SilentlyContinue
            $svcStatus[$svc] = @{{
                Status = $s.Status
                StartType = $s.StartType
                CanStop = $s.CanStop
                ImagePath = $props.ImagePath
            }}
        }}
    }}
    $svcStatus | ConvertTo-Json -Depth 10
    '''

    output = run_powershell(cmd)
    try:
        status['services'] = json.loads(output)
        print(f"  ✓ Collected service status")
    except:
        print(f"  ✗ Could not parse service data")
        status['services'] = {}

    return status


def get_event_log_errors() -> dict:
    """Check for relevant error events."""
    events = {}

    print('Scanning Event Viewer...')

    cmd = '''
    $errors = @()
    Get-EventLog -LogName System -Newest 100 -ErrorAction SilentlyContinue |
        Where-Object { $_.Source -in @('IAStorDataMgrSvc', 'PcaSvc', 'Service Control Manager') -and $_.EntryType -eq 'Error' } |
        ForEach-Object {
            $errors += @{
                TimeGenerated = $_.TimeGenerated
                Source = $_.Source
                EventId = $_.EventId
                Message = $_.Message.Substring(0, [math]::Min(200, $_.Message.Length))
            }
        }

    @{ Errors = $errors; Count = $errors.Count } | ConvertTo-Json -Depth 10
    '''

    output = run_powershell(cmd)
    try:
        result = json.loads(output)
        events['event_errors'] = result.get('Errors', [])
        print(f"  ✓ Found {result.get('Count', 0)} error events")
    except:
        print(f"  ✗ Could not parse event log data")
        events['event_errors'] = []

    return events


def check_wmi_subscriptions() -> dict:
    """Check for WMI event subscriptions."""
    subs = {}

    print('Checking WMI subscriptions...')

    cmd = '''
    $subs = @()
    try {
        Get-WmiObject __EventSubscription -Namespace root\\subscription -ErrorAction SilentlyContinue | ForEach-Object {
            $subs += @{
                Filter = $_.Filter
                Consumer = $_.Consumer
            }
        }
    } catch { }

    @{ Subscriptions = $subs; Count = $subs.Count } | ConvertTo-Json -Depth 10
    '''

    output = run_powershell(cmd)
    try:
        result = json.loads(output)
        subs['subscriptions'] = result.get('Subscriptions', [])
        print(f"  ✓ Found {result.get('Count', 0)} WMI subscriptions")
    except Exception as e:
        print(f"  ✗ Could not query WMI: {e}")
        subs['subscriptions'] = []

    return subs


def check_registry_integrity() -> dict:
    """Check for broken or orphaned registry entries."""
    registry = {}

    print('Checking registry integrity...')

    # Check if CLSID still exists (should be removed)
    clsid_path = f'SOFTWARE\\Classes\\CLSID\\{ENGINE_CLSID}'
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_path):
            registry['clsid_exists'] = True
            print(f"  ✗ CLSID {ENGINE_CLSID} still exists in registry!")
    except FileNotFoundError:
        registry['clsid_exists'] = False
        print(f"  ✓ CLSID {ENGINE_CLSID} not found (good)")

    # Check for orphaned voice registrations
    voices_path = 'SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens'
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, voices_path) as key:
            i = 0
            orphaned_voices = []
            while True:
                try:
                    name = winreg.EnumKey(key, i)
                    if name.startswith('ElevenLabs_'):
                        orphaned_voices.append(name)
                    i += 1
                except OSError:
                    break

            registry['orphaned_voices'] = orphaned_voices
            if orphaned_voices:
                print(f"  ✗ Found {len(orphaned_voices)} orphaned voice tokens!")
            else:
                print(f"  ✓ No orphaned voice tokens found")
    except Exception as e:
        print(f"  ✗ Could not check voice registry: {e}")
        registry['orphaned_voices'] = []

    return registry


def generate_report(data: dict):
    """Generate and save diagnostic report."""
    banner('Diagnostic Report Generated', '─')

    report = {
        'timestamp': datetime.now().isoformat(),
        'diagnosis': data
    }

    # Analyze findings
    issues = []

    if data.get('registry', {}).get('clsid_exists'):
        issues.append("CRITICAL: Engine CLSID still exists in registry")

    if data.get('registry', {}).get('orphaned_voices'):
        issues.append(f"WARNING: Found {len(data['registry']['orphaned_voices'])} orphaned voice tokens")

    if data.get('events', {}).get('event_errors'):
        issues.append(f"WARNING: Found {len(data['events']['event_errors'])} error events")

    report['detected_issues'] = issues

    # Save report
    try:
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        print(f'✓ Report saved to: {REPORT_FILE}')
    except Exception as e:
        print(f'✗ Could not save report: {e}')

    # Print summary
    print('\n' + '='*60)
    print('DIAGNOSTIC SUMMARY')
    print('='*60)

    if not issues:
        print('✅ No critical issues detected.')
        print('\nThe system appears to be clean of SAPI Bridge artifacts.')
        print('High CPU consumption may be due to:')
        print('  1. Intel Rapid Storage Technology driver issue')
        print('  2. Windows indexing or background tasks')
        print('  3. Unrelated system issue (run anti-malware scan)')
    else:
        print('\n⚠️  ISSUES DETECTED:\n')
        for i, issue in enumerate(issues, 1):
            print(f'{i}. {issue}')

    print('\n' + '='*60)
    print('NEXT STEPS')
    print('='*60)
    print('If issues remain:')
    print('  1. Run: sfc /scannow (System File Checker)')
    print('  2. Check for Intel Rapid Storage driver updates')
    print('  3. Run anti-malware scan (Windows Defender full scan)')
    print('  4. Check Device Manager for driver warnings')


def main():
    banner('CPU Usage Diagnostic Tool')

    print('Step 1: Verifying Administrator privileges…')
    check_admin()
    print('  ✓ Running as Administrator\n')

    all_data = {}

    print('Step 2: Process Analysis')
    all_data['processes'] = get_process_details()

    print('\nStep 3: Service Status')
    all_data['services'] = get_service_status()

    print('\nStep 4: Event Log Analysis')
    all_data['events'] = get_event_log_errors()

    print('\nStep 5: WMI Subscriptions')
    all_data['wmi'] = check_wmi_subscriptions()

    print('\nStep 6: Registry Integrity')
    all_data['registry'] = check_registry_integrity()

    # Generate report
    generate_report(all_data)


if __name__ == '__main__':
    main()
