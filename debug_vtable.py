"""
Debug script to check if vtables are being created correctly for our interfaces.
"""

import sys
sys.path.insert(0, r'E:\##Development\Windows-SAPI-Bridge-for-ElevenLabs')

import ctypes
from elevenlabs_engine import (
    ElevenLabsTTSEngine, ISpTTSEngine, ISpObjectWithToken,
    IID_ISpTTSEngine, IID_ISpObjectWithToken
)

# Create an engine instance
engine = ElevenLabsTTSEngine()

print("Engine created successfully")
print(f"_com_pointers_ keys: {list(engine._com_pointers_.keys())}")

# Check ISpTTSEngine pointer
sp_tts_ptr = engine._com_pointers_.get(IID_ISpTTSEngine)
print(f"\nISpTTSEngine pointer: {sp_tts_ptr}")

if sp_tts_ptr:
    # Dereference the pointer twice (pointer to pointer to vtable)
    try:
        pp = ctypes.cast(sp_tts_ptr, ctypes.POINTER(ctypes.c_void_p))
        p = pp[0]  # Get the first pointer (pointer to vtable)
        print(f"  Dereferenced to: {ctypes.c_void_p(p)}")

        # Now p is a pointer to the vtable
        # Dereference it to get the vtable entries
        vtbl_ptr = ctypes.cast(p, ctypes.POINTER(ctypes.c_void_p))
        print(f"  VTable at: {ctypes.c_void_p(p)}")

        # Print first few vtable entries (should be QueryInterface, AddRef, Release, Speak, GetOutputFormat)
        print("  VTable entries:")
        for i in range(5):
            fn_ptr = vtbl_ptr[i]
            print(f"    [{i}]: {ctypes.c_void_p(fn_ptr)}")
    except Exception as e:
        print(f"  Error dereferencing: {e}")

# Check ISpObjectWithToken pointer
sp_obj_ptr = engine._com_pointers_.get(IID_ISpObjectWithToken)
print(f"\nISpObjectWithToken pointer: {sp_obj_ptr}")

if sp_obj_ptr:
    try:
        pp = ctypes.cast(sp_obj_ptr, ctypes.POINTER(ctypes.c_void_p))
        p = pp[0]
        print(f"  Dereferenced to: {ctypes.c_void_p(p)}")

        vtbl_ptr = ctypes.cast(p, ctypes.POINTER(ctypes.c_void_p))
        print(f"  VTable at: {ctypes.c_void_p(p)}")

        print("  VTable entries:")
        for i in range(5):
            fn_ptr = vtbl_ptr[i]
            print(f"    [{i}]: {ctypes.c_void_p(fn_ptr)}")
    except Exception as e:
        print(f"  Error dereferencing: {e}")

print("\nDone")
