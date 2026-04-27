# SAPI5 Engine Status & Investigation Results

## Current State
- **Engine Registration**: ✅ Working - COM engine properly registered in Windows registry
- **Interface Discovery**: ✅ Working - ISpTTSEngine and ISpObjectWithToken queries return S_OK
- **VTable Creation**: ✅ Working - Valid function pointers created for all methods
- **Method Invocation**: ❌ Not working - Methods are never called by COM clients

## What We've Verified
1. Engine instantiates correctly through COM
2. Interfaces have valid vtable entries with non-NULL function pointers
3. SAPI applications successfully query for and find both interfaces
4. Config files are valid JSON
5. Voice registration completes successfully (45+ voices)
6. All SAPI structure definitions (SPVSTATE, SPVTEXTFRAG, WAVEFORMATEX) have correct sizes

## Root Cause Identified
**Comtypes' LocalServer32 method marshaling limitation**: While comtypes creates interface pointers with valid vtables, the marshaling layer doesn't properly route method invocations from native COM clients to Python methods. 

This manifests as:
- QueryInterface succeeds (basic COM protocol works)
- SAPI apps get the interface pointers
- But SetObjectToken, Speak, GetOutputFormat are never called
- SAPI apps then query for additional interfaces (like a type descriptor)
- When those fail, they release and give up

## Why It's Hard to Fix
The issue is deep in comtypes' COM marshaling infrastructure. Python methods need to be wrapped in COM-callable function pointers that respect Windows calling conventions. While comtypes does this, something in the process prevents method dispatch from working correctly for LocalServer32 implementations.

Potential solutions would require:
1. Rewriting parts of comtypes to handle method dispatch differently
2. Implementing the engine in C/C++ instead of Python
3. Using a different COM framework (like pywin32 or C#)
4. Using IDispatch + type libraries for runtime method discovery

## Next Steps: WinRT Migration
Given:
- The original plan was to "mark SAPI as legacy and shift to WinRT/C#"
- Fixing this would require deep infrastructure changes
- WinRT/C# is more modern and better supported for this use case

**Recommendation**: Move forward with the WinRT implementation as originally planned. The Python/comtypes approach has fundamental limitations for exposing COM methods to native clients in LocalServer32 mode.

## Files for Reference
- `elevenlabs_engine.py` - The COM engine implementation
- `install_voices.py` - Voice registration script
- `config.example.json` / `config.json` - Configuration
- Engine logs: `%APPDATA%\ElevenLabsSAPI\engine.log`
