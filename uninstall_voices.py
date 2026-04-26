"""
Windows SAPI Bridge for ElevenLabs — Voice Uninstaller
========================================================
Removes all ElevenLabs SAPI voice registrations created by install_voices.py.

MUST be run as Administrator.
Usage:  python uninstall_voices.py
"""

import sys
import os
import json
import ctypes

try:
    import winreg
except ImportError:
    print('ERROR: This script must be run on Windows.')
    sys.exit(1)

_script_dir  = os.path.dirname(os.path.abspath(__file__))
_state_path  = os.path.join(_script_dir, '.installed_voices.json')

SPEECH_VOICES = r'SOFTWARE\Microsoft\Speech\Voices\Tokens'
CLASSES_CLSID = r'SOFTWARE\Classes\CLSID'
_ACCESS = winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY


def delete_tree(hive, path: str):
    """Recursively delete a registry key and all its sub-keys."""
    try:
        with winreg.OpenKey(hive, path, 0, _ACCESS) as k:
            while True:
                try:
                    sub = winreg.EnumKey(k, 0)
                    delete_tree(hive, f'{path}\\{sub}')
                except OSError:
                    break
        winreg.DeleteKey(hive, path)
        print(f'  Deleted: HKLM\\{path}')
    except FileNotFoundError:
        print(f'  Skipped (not found): HKLM\\{path}')
    except OSError as exc:
        print(f'  WARNING: Could not delete HKLM\\{path}: {exc}')


def main():
    print('╔══════════════════════════════════════════════════════════╝')
    print('║   Windows SAPI Bridge for ElevenLabs — Voice Uninstaller ║')
    print('╚══════════════════════════════════════════════════════════╝')

    if not ctypes.windll.shell32.IsUserAnAdmin():
        print('\nERROR: Must be run as Administrator.')
        sys.exit(1)

    if not os.path.exists(_state_path):
        print('\nNo install record found — nothing to uninstall.')
        return

    with open(_state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)

    voices       = state.get('voices', [])
    engine_clsid = state.get('engine_clsid', '')

    print(f'\nRemoving {len(voices)} voice token(s)…')
    for token_key in voices:
        delete_tree(winreg.HKEY_LOCAL_MACHINE, f'{SPEECH_VOICES}\\{token_key}')

    if engine_clsid:
        print('\nRemoving engine CLSID…')
        delete_tree(winreg.HKEY_LOCAL_MACHINE, f'{CLASSES_CLSID}\\{engine_clsid}')

    os.remove(_state_path)
    print('\n✅  Uninstall complete.')
    print('ElevenLabs voices have been removed from Windows SAPI.')
    print('Restart any open SAPI applications to see the change.')


if __name__ == '__main__':
    main()
