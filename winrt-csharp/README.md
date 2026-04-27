# Windows SAPI Bridge for ElevenLabs — WinRT/C# Implementation

This directory contains the modern WinRT/C# implementation of the ElevenLabs TTS engine for Windows SAPI5, replacing the Python/comtypes version that reached fundamental technical limitations.

## Why WinRT/C#?

The original Python implementation using comtypes encountered a core limitation: LocalServer32 method marshaling in comtypes cannot properly route method invocations from native COM clients to Python methods. While interfaces are discovered and vtables are valid, actual method calls never reach Python code.

**WinRT/C# provides:**
- Native .NET COM interop with proper method dispatch
- Better Windows API integration (registry, audio streaming)
- Modern async/await patterns
- Type safety and compile-time checking
- Easier debugging and logging
- Proper SAPI5 interface implementation

## Architecture

```
ElevenLabsTTSEngine/
├── ElevenLabsTTSEngine.csproj  # Main project configuration
├── TTSEngine.cs                # Core engine implementation
├── ComInterfaces.cs            # SAPI5 COM interface definitions
└── [Future components]

Tests/
├── ElevenLabsTTSEngine.Tests.csproj  # Test project
└── EngineTests.cs              # Unit tests
```

## Key Components

### TTSEngine.cs
The main engine class that:
- Initializes with configuration (API key, TTS parameters)
- Loads voice mappings from ElevenLabs API
- Synthesizes audio streams using ElevenLabs API
- Handles SAPI5 interface implementation

### ComInterfaces.cs
COM interface definitions for SAPI5 integration:
- `ISpTTSEngine` - Core TTS engine interface
- `ISpObjectWithToken` - Token/voice management
- `WAVEFORMATEX` - Audio format specification

## Development Plan

### Phase 1: Core Engine (Current)
- [ ] Implement configuration loading (JSON parsing)
- [ ] Implement ElevenLabs API voice fetching
- [ ] Implement audio synthesis with rate scaling
- [ ] Create basic unit tests

### Phase 2: SAPI5 Integration
- [ ] Implement COM registration
- [ ] Implement voice registration in Windows registry
- [ ] Implement ISpTTSEngine methods (Speak, GetOutputFormat)
- [ ] Implement ISpObjectWithToken methods (SetObjectToken)

### Phase 3: Testing & Refinement
- [ ] Integration tests with real SAPI5 applications
- [ ] Test with screen readers (NVDA, Narrator)
- [ ] Test with e-book readers (Calibre)
- [ ] Performance optimization

### Phase 4: Deployment
- [ ] Installer creation
- [ ] Documentation
- [ ] Release to GitHub

## Building

### Prerequisites
- Visual Studio 2022 or later
- .NET 6.0 SDK (or later)
- Windows 10/11 (21H2 or later recommended)

### Build
```bash
cd winrt-csharp
dotnet build
```

### Run Tests
```bash
dotnet test
```

## Configuration

The engine expects a `config.json` file (based on the SAPI5 implementation):

```json
{
    "api_key": "sk_...",
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0,
    "use_speaker_boost": false,
    "speed": 1.0,
    "sapi_rate_scaling": true
}
```

See `../config.example.json` for a template.

## API Reference

### ElevenLabsTTSEngine Class

#### InitializeAsync(string configPath)
Initialize the engine with configuration.

**Parameters:**
- `configPath`: Path to config.json file

**Returns:** IAsyncAction

#### SynthesizeAsync(string text, string voiceId, float rate)
Synthesize text to speech.

**Parameters:**
- `text`: Text to synthesize
- `voiceId`: ElevenLabs voice ID
- `rate`: Speech rate multiplier (1.0 = normal speed)

**Returns:** IAsyncOperation<byte[]> containing raw PCM audio

#### RegisterVoicesAsync()
Register ElevenLabs voices in Windows SAPI voice list.

**Returns:** IAsyncAction

## Debugging

Logs are written to the Windows debug output and can be viewed in:
- Visual Studio Debug Output window
- Windows Event Viewer (Application logs)
- Debugview utility

## References

- [SAPI5 Documentation](https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms723627)
- [Windows.Media.SpeechSynthesis](https://docs.microsoft.com/en-us/uwp/api/windows.media.speechsynthesis)
- [ElevenLabs API Documentation](https://api.elevenlabs.io/docs)
- [COM in .NET](https://docs.microsoft.com/en-us/dotnet/framework/interop/exposing-com-components-to-the-net-framework)

## Legacy Code

The original Python implementation is preserved in the parent directory for reference:
- `elevenlabs_engine.py` - Original SAPI5 COM engine
- `install_voices.py` - Voice registration script
- `SAPI_STATUS.md` - Investigation findings and limitations

See [../SAPI_STATUS.md](../SAPI_STATUS.md) for details about why the Python approach was limited.
