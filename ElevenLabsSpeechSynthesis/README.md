# ElevenLabs Speech Synthesis Platform

A unified, decentralized speech synthesis platform for Windows that brings ElevenLabs voices to **every application** on your system through a local service and plugin ecosystem.

## Vision

**Install once. Configure once. Use everywhere.**

Rather than per-application setup or relying on deprecated SAPI5, this platform provides a modern, extensible local service that any Windows application can integrate with through simple plugins.

## What It Does

1. **Local Service** — Runs as a Windows Service, handles all ElevenLabs TTS synthesis
2. **Unified API** — REST API on localhost:11776 for synthesis requests
3. **Plugin Ecosystem** — Applications integrate via plugins:
   - Calibre (e-book reader)
   - NVDA (screen reader)
   - Windows.Media.SpeechSynthesis (modern Windows apps)
   - More to come
4. **User-Owned Keys** — Each user provides their own ElevenLabs API key (no centralized backend)

## Features

✅ **Modern Architecture**
- Replaces deprecated SAPI5 with forward-compatible local service
- REST API for easy integration
- Async/await throughout

✅ **User Control**
- Encrypted API key storage (Windows DPAPI)
- Local-only communication (no data leaves your machine except API calls)
- Full quota tracking and usage reporting
- User manages their API key and usage

✅ **Multi-Application Support**
- Works with Calibre, NVDA, modern Windows apps
- Extensible plugin system for additional applications
- Single configuration for all applications

✅ **Developer Friendly**
- Clean REST API
- Example plugin implementations
- Comprehensive documentation
- Easy to add new application plugins

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design, data flows, and component descriptions.

**Quick Overview:**
```
Applications (Calibre, NVDA, etc.)
        ↓
    Plugins
        ↓
  REST API (localhost:11776)
        ↓
 Local Service (Windows Service)
        ↓
  ElevenLabs API
```

## Installation (Coming Soon)

**Prerequisites:**
- Windows 10/11 (64-bit)
- .NET 6.0 Runtime (included in installer)
- ElevenLabs account + API key

**Steps:**
1. Download ElevenLabsSpeechSynthesis-Setup.exe
2. Run installer (admin required for service)
3. During setup, enter your ElevenLabs API key
4. Choose which plugins to install (Calibre, NVDA, etc.)
5. Restart applications
6. Choose ElevenLabs voices in your app's voice settings

## Configuration

After installation, configuration is stored in:
```
%APPDATA%\ElevenLabsSpeechSynthesis\config.json
```

**Example config:**
```json
{
  "api_key": "sk_... (encrypted)",
  "stability": 0.5,
  "similarity_boost": 0.75,
  "style": 0,
  "use_speaker_boost": false,
  "speed": 1.0,
  "cache_voices": true,
  "voice_cache_ttl_hours": 24,
  "enable_usage_tracking": true,
  "port": 11776,
  "log_level": "info"
}
```

Change settings anytime without restarting — the service auto-detects config changes.

## Using ElevenLabs Voices

### In Calibre
1. Open any book
2. Click "Read Aloud" or use keyboard shortcut
3. Select voice → Choose any "ElevenLabs - [Voice Name]" voice
4. Click Speak

### In NVDA
1. Open NVDA Settings → Speech → Speech Synthesizer
2. Select "ElevenLabs Speech Synthesis"
3. Choose desired voice from the list
4. NVDA will use ElevenLabs for all speech output

### In Modern Windows Apps
Any app using Windows.Media.SpeechSynthesis will see ElevenLabs voices alongside built-in voices.

## REST API (For Developers)

### Endpoints

**Get Available Voices**
```
GET /api/voices
```
Response:
```json
[
  {
    "id": "1",
    "name": "Bella",
    "accent": "British",
    "category": "female"
  },
  ...
]
```

**Synthesize Text**
```
POST /api/synthesize
{
  "text": "Hello world",
  "voice_id": "1",
  "stability": 0.5,
  "similarity_boost": 0.75,
  "style": 0,
  "use_speaker_boost": false
}
```
Response: Audio bytes (raw PCM audio)

**Get Status**
```
GET /api/status
```
Response: Service health and configuration

**Get Usage**
```
GET /api/usage
```
Response:
```json
{
  "characters_used": 15000,
  "character_limit": 100000,
  "characters_remaining": 85000,
  "tier": "Professional",
  "percentage_used": 15.0
}
```

**Reload Configuration**
```
POST /api/config/reload
```

## Creating a Plugin

Creating a plugin is straightforward:

```csharp
using ElevenLabsSpeechSynthesis.Plugins.Common;

public class MyAppPlugin
{
    private ServiceDiscovery _service = new ServiceDiscovery();
    
    public async Task Speak(string text, string voiceId)
    {
        var available = await _service.IsServiceAvailableAsync();
        if (!available) return; // Fallback to built-in TTS
        
        var audio = await _service.PostAsync<SynthesisRequest, byte[]>(
            "/synthesize",
            new { text, voiceId }
        );
        
        PlayAudio(audio);
    }
}
```

See [Plugins/WindowsMediaSpeechSynthesis/VoiceProvider.cs](Plugins/WindowsMediaSpeechSynthesis/VoiceProvider.cs) for a complete example.

## Project Structure

```
ElevenLabsSpeechSynthesis/
├── Core/
│   ├── Configuration.cs          # Config loading/saving (encrypted API key)
│   ├── ElevenLabsApiClient.cs    # HTTP client for ElevenLabs API
│   ├── Logging.cs                # Serilog setup
│   └── ElevenLabsSpeechSynthesis.Core.csproj
│
├── Service/
│   ├── Program.cs                # Service entry point
│   ├── ServiceWorker.cs           # Hosted service (Windows Service)
│   ├── SynthesisService.cs        # Core synthesis logic
│   └── ElevenLabsSpeechSynthesis.Service.csproj
│
├── Plugins/
│   ├── Common/
│   │   ├── ServiceDiscovery.cs   # Find/communicate with service
│   │   └── ElevenLabsSpeechSynthesis.Plugins.Common.csproj
│   │
│   ├── WindowsMediaSpeechSynthesis/
│   │   ├── VoiceProvider.cs      # Modern Windows API provider
│   │   └── ElevenLabsSpeechSynthesis.Plugins.WindowsMedia.csproj
│   │
│   ├── Calibre/                  # TODO: Python plugin for Calibre
│   └── NVDA/                     # TODO: Python add-on for NVDA
│
├── Installer/                    # TODO: WiX/NSIS installer
├── ARCHITECTURE.md               # System design and data flows
├── README.md                     # This file
└── ElevenLabsSpeechSynthesis.sln # Solution file
```

## Development

### Prerequisites
- Visual Studio 2022 or VS Code
- .NET 6.0 SDK
- Git

### Build
```bash
cd ElevenLabsSpeechSynthesis
dotnet build
```

### Run Service (Debug)
```bash
cd Service
dotnet run
```

### Test
```bash
# Tests coming soon
```

## Development Phases

- [x] **Phase 1** - Architecture & Core Library
  - Core project structure
  - Configuration management
  - API client implementation
  - Logging setup

- [ ] **Phase 2** - Service & REST API
  - Windows Service boilerplate
  - REST API endpoints
  - Voice caching
  - Synthesis routing

- [ ] **Phase 3** - Plugins
  - Calibre plugin (Python)
  - NVDA add-on (Python)
  - Windows.Media.SpeechSynthesis provider (C#)

- [ ] **Phase 4** - Installer
  - MSI/NSIS installer creation
  - Configuration wizard
  - Auto-start service
  - Plugin bundling

- [ ] **Phase 5** - Testing
  - Integration tests
  - Real-world application testing
  - Performance testing

- [ ] **Phase 6** - Documentation & Release
  - User guide
  - Developer guide
  - Plugin development samples
  - Public release

## Comparing: SAPI5 vs. This Platform

| Aspect | SAPI5 | Platform |
|--------|-------|----------|
| **Technology** | Legacy (1990s) | Modern (2024+) |
| **Status** | Being deprecated | Future-proof |
| **Supported Apps** | Only SAPI5-aware apps | Any app (via plugins) |
| **Configuration** | Per-application | Once, system-wide |
| **Quota Tracking** | None | Built-in |
| **Extensibility** | Limited | Plugin ecosystem |
| **Security** | System-level | User-level + encrypted |

## Future Enhancements

- Web dashboard for configuration and usage tracking
- Voice cloning support (custom model training)
- Real-time transcription pipeline (speech-to-text)
- Additional application plugins
- Cloud backup of configuration
- Mobile app integration (WinRT → Windows Phone/Tablet)
- Offline mode (voice model caching)

## Troubleshooting

**Service not starting?**
- Check Windows Services (services.msc) for "ElevenLabsSpeechSynthesis"
- Review logs in `%APPDATA%\ElevenLabsSpeechSynthesis\service.log`
- Ensure .NET 6.0 Runtime is installed

**Plugins not finding service?**
- Service must be running (check Services)
- Port 11776 must be open
- Default to built-in TTS if service is unavailable

**API key errors?**
- Verify API key is valid at elevenlabs.io
- Check for quota/billing issues
- Review logs for specific error messages

## License

[MIT License](../../LICENSE)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Submit a pull request

## Support

Issues and questions: [GitHub Issues](https://github.com/xTaraRose/Windows-SAPI-Bridge-for-ElevenLabs/issues)

## Roadmap

- **Q2 2024**: Core service + Calibre plugin
- **Q3 2024**: NVDA plugin + Windows.Media.SpeechSynthesis provider
- **Q4 2024**: Installer + public beta release
- **2025**: Community plugins, advanced features

---

**Built by [@xTaraRose](https://github.com/xTaraRose)**

Turning ElevenLabs into the speech engine for Windows.
