"""
Test client to verify if COM method invocation works on the ElevenLabs engine.
This creates the object directly and tries to call methods.
"""

import sys
import os
import ctypes
import time

# Add the script directory to the path
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _script_dir)

import comtypes
from comtypes import CoCreateInstance
from comtypes.client import GetModule

# Import our GUIDs
from elevenlabs_engine import (
    CLSID_ElevenLabsEngine, IID_ISpTTSEngine, IID_ISpObjectWithToken,
    ISpTTSEngine, ISpObjectWithToken, WAVEFORMATEX
)

def test_direct_creation():
    """Try to directly instantiate the engine."""
    print("=" * 60)
    print("Test 1: Direct CoCreateInstance")
    print("=" * 60)

    try:
        # Try to create the engine
        engine = CoCreateInstance(
            CLSID_ElevenLabsEngine,
            interface=comtypes.IUnknown,
            clsctx=comtypes.CLSCTX_LOCAL_SERVER
        )
        print(f"[OK] Created engine: {engine}")

        # Try to get ISpObjectWithToken
        try:
            token_iface = engine.QueryInterface(ISpObjectWithToken)
            print(f"[OK] Got ISpObjectWithToken: {token_iface}")

            # Try to call SetObjectToken with NULL
            print("  Attempting SetObjectToken(NULL)...")
            result = token_iface.SetObjectToken(None)
            print(f"  SetObjectToken result: {result}")
        except Exception as e:
            print(f"[FAIL] ISpObjectWithToken failed: {e}")

        # Try to get ISpTTSEngine
        try:
            engine_iface = engine.QueryInterface(ISpTTSEngine)
            print(f"[OK] Got ISpTTSEngine: {engine_iface}")

            # Try to call GetOutputFormat with NULL params
            print("  Attempting GetOutputFormat(NULL, NULL, NULL, NULL)...")
            result = engine_iface.GetOutputFormat(None, None, None, None)
            print(f"  GetOutputFormat result: {result}")
        except Exception as e:
            print(f"[FAIL] ISpTTSEngine failed: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"[FAIL] Failed to create engine: {e}")
        import traceback
        traceback.print_exc()

def test_via_registry():
    """Try to create the engine via registry lookup."""
    print("\n" + "=" * 60)
    print("Test 2: Via Registry Lookup")
    print("=" * 60)

    try:
        # Try to get the type library first
        print(f"CLSID: {CLSID_ElevenLabsEngine}")

        # Create with GetModule to get type info
        comtypes.CoInitialize()
        engine = CoCreateInstance(
            CLSID_ElevenLabsEngine,
            clsctx=comtypes.CLSCTX_LOCAL_SERVER
        )
        print(f"[OK] Created engine via CoCreateInstance")

        # Check what interfaces are supported
        for iid_name, iid in [
            ('ISpObjectWithToken', IID_ISpObjectWithToken),
            ('ISpTTSEngine', IID_ISpTTSEngine),
        ]:
            try:
                iface = engine.QueryInterface(iid)
                print(f"[OK] {iid_name} supported")
            except comtypes.COMError as e:
                print(f"[FAIL] {iid_name}: {e}")

        comtypes.CoUninitialize()
    except Exception as e:
        print(f"[FAIL] Registry test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("\nTesting COM method invocation on ElevenLabs engine...\n")

    # Give engine time to start if needed
    time.sleep(0.5)

    test_direct_creation()
    test_via_registry()

    print("\n" + "=" * 60)
    print("Test complete. Check %APPDATA%\\ElevenLabsSAPI\\engine.log")
    print("=" * 60)
