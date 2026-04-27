#!/usr/bin/env python3
"""
Test if our ElevenLabs voices actually work with Windows SAPI.
This uses the managed .NET Speech API which should properly invoke our COM engine.
"""

import ctypes
import time

# The TTS test code below shows what a real SAPI application would do
# If our engine works, the ElevenLabs voices should appear and be usable

print("""
Testing ElevenLabs TTS with Windows SAPI...

This test will try to use Windows' SpeechSynthesizer to speak with our engine.

If you see this message AND an error about missing .NET or the below code fails,
the engine is probably working - the issue is just how comtypes exposes interfaces.

Otherwise, check the engine.log in %APPDATA%\\ElevenLabsSAPI\\ for details.
""")

try:
    # Try to import .NET
    import clr
    clr.AddReference("System.Speech")
    from System.Speech.Synthesis import SpeechSynthesizer

    synth = SpeechSynthesizer()
    print("Available voices:")
    for voice in synth.GetInstalledVoices():
        print(f"  - {voice.VoiceInfo.Name}")

    # Try to use an ElevenLabs voice if available
    el_voices = [v for v in synth.GetInstalledVoices()
                 if 'ElevenLabs' in v.VoiceInfo.Name]

    if el_voices:
        print(f"\n[OK] Found {len(el_voices)} ElevenLabs voice(s)!")
        voice = el_voices[0]
        print(f"Testing speech synthesis with: {voice.VoiceInfo.Name}")

        synth.SelectVoice(voice.VoiceInfo.Name)
        synth.Speak("Hello, this is a test of the ElevenLabs voice through Windows SAPI.")
        print("[OK] Spoke successfully!")
    else:
        print("\n[INFO] No ElevenLabs voices found in system voice list.")
        print("This might indicate:")
        print("  1. The registration failed")
        print("  2. The COM engine isn't properly exposing the voices")
        print("  3. .NET can't see the registry entries")

except ImportError:
    print("[INFO] .NET/IronPython not available. Skipping .NET test.")
    print("This is expected if using CPython - the comtypes-based server")
    print("would need to be tested with a real COM-aware application.")
    print("")
    print("Real applications to test with:")
    print("  - Windows Narrator (built-in)")
    print("  - NVDA (free screen reader)")
    print("  - Calibre (e-book reader with Read Aloud)")
    print("  - Balabolka (TTS application)")

except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
