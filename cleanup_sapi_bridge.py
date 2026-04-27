"""
Windows SAPI Bridge for ElevenLabs — Emergency Cleanup Script
==============================================================
Comprehensive cleanup utility that removes all traces of the SAPI Bridge
installation, including registry entries, COM objects, and configuration files.

This script is useful when:
- The standard uninstall_voices.py fails or doesn't fully clean up
- The .installed_voices.json state file is missing or corrupted
- Manual registry cleanup is needed
- Troubleshooting persistent registry entries or services

MUST be run as Administrator.
Usage:  python cleanup_sapi_bridge.py

WARNING: This script modifies the Windows registry. It is recommended to
create a system restore point before running this script.
"""

import sys
import os
import json
import ctypes
import argparse
import io

# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import winreg
except ImportError:
    print('ERROR: This script must be run on Windows.')
    sys.exit(1)


# ─── Constants ────────────────────────────────────────────────────────────────

ENGINE_CLSID = '{6C0A3A4E-8F2B-4E5D-A3C7-1B9F2E8D4A6C}'
SPEECH_VOICES = r'SOFTWARE\Microsoft\Speech\Voices\Tokens'
CLASSES_CLSID = r'SOFTWARE\Classes\CLSID'
_ACCESS = winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY

_script_dir = os.path.dirname(os.path.abspath(__file__))
_state_path = os.path.join(_script_dir, '.installed_voices.json')
_config_path = os.path.join(_script_dir, 'config.json')


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
        print('Please right-click Command Prompt → Run as administrator, then try again.')
        sys.exit(1)


def delete_registry_key(hive, path: str) -> bool:
    """Recursively delete a registry key and all its sub-keys."""
    try:
        with winreg.OpenKey(hive, path, 0, _ACCESS) as k:
            while True:
                try:
                    sub = winreg.EnumKey(k, 0)
                    delete_registry_key(hive, f'{path}\\{sub}')
                except OSError:
                    break
        winreg.DeleteKey(hive, path)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def find_elevenlabs_voices() -> list:
    """Find all ElevenLabs voice registrations in the registry."""
    voices = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, SPEECH_VOICES, 0, winreg.KEY_READ) as k:
            i = 0
            while True:
                try:
                    name = winreg.EnumKey(k, i)
                    if name.startswith('ElevenLabs_'):
                        voices.append(name)
                    i += 1
                except OSError:
                    break
    except FileNotFoundError:
        pass
    return voices


def cleanup_voices(verbose: bool = False) -> int:
    """Remove all ElevenLabs voice registrations."""
    voices = find_elevenlabs_voices()

    if not voices:
        print('  ✓ No ElevenLabs voice registrations found.')
        return 0

    print(f'  Removing {len(voices)} voice registration(s)…')
    removed = 0

    for voice_token in voices:
        key_path = f'{SPEECH_VOICES}\\{voice_token}'
        if delete_registry_key(winreg.HKEY_LOCAL_MACHINE, key_path):
            if verbose:
                print(f'    ✓ Removed: {voice_token}')
            removed += 1
        else:
            if verbose:
                print(f'    ✗ Failed to remove: {voice_token}')

    print(f'  ✓ Successfully removed {removed} voice registration(s).')
    return removed


def cleanup_clsid(verbose: bool = False) -> bool:
    """Remove the ElevenLabs engine CLSID registration."""
    clsid_path = f'{CLASSES_CLSID}\\{ENGINE_CLSID}'

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_path, 0, winreg.KEY_READ):
            pass
    except FileNotFoundError:
        print('  ✓ No ElevenLabs engine CLSID found.')
        return False

    print(f'  Removing engine CLSID: {ENGINE_CLSID}')

    if delete_registry_key(winreg.HKEY_LOCAL_MACHINE, clsid_path):
        print('  ✓ Successfully removed engine CLSID.')
        return True
    else:
        print('  ✗ Failed to remove engine CLSID (may already be deleted).')
        return False


def cleanup_state_file() -> bool:
    """Remove the installation state file."""
    if not os.path.exists(_state_path):
        print('  ✓ No state file found.')
        return False

    try:
        os.remove(_state_path)
        print(f'  ✓ Removed state file: {_state_path}')
        return True
    except Exception as e:
        print(f'  ✗ Failed to remove state file: {e}')
        return False


def cleanup_config_file(preserve: bool = False) -> bool:
    """Remove the configuration file (optionally preserve API key)."""
    if not os.path.exists(_config_path):
        print('  ✓ No configuration file found.')
        return False

    if preserve:
        print(f'  → Preserving config file (as requested): {_config_path}')
        return False

    try:
        os.remove(_config_path)
        print(f'  ✓ Removed configuration file: {_config_path}')
        return True
    except Exception as e:
        print(f'  ✗ Failed to remove configuration file: {e}')
        return False


def verify_cleanup() -> bool:
    """Verify that all SAPI Bridge registrations have been removed."""
    voices = find_elevenlabs_voices()

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f'{CLASSES_CLSID}\\{ENGINE_CLSID}', 0, winreg.KEY_READ):
            clsid_exists = True
    except FileNotFoundError:
        clsid_exists = False

    state_exists = os.path.exists(_state_path)

    return len(voices) == 0 and not clsid_exists and not state_exists


def main():
    parser = argparse.ArgumentParser(
        description='Emergency cleanup for Windows SAPI Bridge for ElevenLabs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python cleanup_sapi_bridge.py                    # Full cleanup
  python cleanup_sapi_bridge.py --preserve-config  # Keep config.json
  python cleanup_sapi_bridge.py --verbose          # Show detailed progress
        '''
    )
    parser.add_argument(
        '--preserve-config',
        action='store_true',
        help='Preserve config.json file (default: remove it)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show detailed cleanup progress'
    )

    args = parser.parse_args()

    banner('Windows SAPI Bridge Cleanup Utility')

    # Check admin privileges
    print('Step 1: Verifying Administrator privileges…')
    check_admin()
    print('  ✓ Running as Administrator\n')

    # Perform cleanup
    print('Step 2: Removing SAPI Bridge registrations…')
    voices_removed = cleanup_voices(verbose=args.verbose)
    clsid_removed = cleanup_clsid(verbose=args.verbose)

    print('\nStep 3: Removing installation state file…')
    state_removed = cleanup_state_file()

    print('\nStep 4: Handling configuration file…')
    config_removed = cleanup_config_file(preserve=args.preserve_config)

    # Verify cleanup
    print('\nStep 5: Verifying cleanup…')
    if verify_cleanup():
        print('  ✓ Cleanup verification PASSED')
        print('  ✓ All SAPI Bridge registrations have been removed.')
    else:
        remaining_voices = find_elevenlabs_voices()
        print('  ✗ Cleanup verification FAILED')
        if remaining_voices:
            print(f'  ✗ {len(remaining_voices)} voice registration(s) still present')

    # Summary
    banner('Cleanup Summary', '─')
    print(f'Voice registrations removed: {voices_removed}')
    print(f'Engine CLSID removed: {"Yes" if clsid_removed else "No"}')
    print(f'State file removed: {"Yes" if state_removed else "No"}')
    print(f'Config file removed: {"Yes" if config_removed else "No (preserved)"}')

    if verify_cleanup():
        print('\n✅  Cleanup completed successfully!')
        print('\nNext steps:')
        print('  1. Restart any SAPI-compatible applications (Narrator, Calibre, NVDA, etc.)')
        print('  2. The ElevenLabs voices should no longer appear in voice selection menus')
        print('  3. If you wish to reinstall, run: python install_voices.py')
        return 0
    else:
        print('\n⚠️  Cleanup completed with warnings.')
        print('\nIf you still experience issues:')
        print('  1. Restart your computer')
        print('  2. Run this script again')
        print('  3. If problems persist, check Event Viewer for errors')
        return 1


if __name__ == '__main__':
    sys.exit(main())
