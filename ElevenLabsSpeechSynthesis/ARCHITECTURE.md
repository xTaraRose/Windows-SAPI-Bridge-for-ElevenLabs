# ElevenLabs Speech Synthesis Platform — Architecture

A unified, decentralized speech synthesis platform for Windows that allows any application to use ElevenLabs voices through a local service and plugin ecosystem.

## Vision

Users install once, configure their ElevenLabs API key once, and every compatible application on their system automatically gains access to ElevenLabs voices — without per-application setup or API key sharing.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Windows Applications                      │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────┐             │
│  │  Calibre     │  │   NVDA     │  │ Other Apps   │             │
│  └──────┬───────┘  └─────┬──────┘  └──────┬───────┘             │
└─────────┼──────────────────┼────────────────┼──────────────────┘
          │                  │                │
┌─────────┼──────────────────┼────────────────┼──────────────────┐
│  Plugin Layer (Bridges)                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐│
│  │ Calibre Plugin   │  │ NVDA Plugin      │  │ WinRT Provider ││
│  └──────┬───────────┘  └─────────┬────────┘  └────────┬───────┘│
└─────────┼────────────────────────┼─────────────────────┼───────┘
          │                        │                     │
          └────────────┬───────────┴─────────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │   REST API / IPC Interface  │
        │   (localhost:11776)         │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────────────────────────┐
        │   ElevenLabs Speech Synthesis Service           │
        │  (Windows Service / Background Task)           │
        │                                                 │
        │  ┌─────────────────────────────────────────┐   │
        │  │ Audio Processing & Streaming            │   │
        │  │ - Text → Synthesis                      │   │
        │  │ - Rate scaling                          │   │
        │  │ - Audio buffering                       │   │
        │  └─────────────────────────────────────────┘   │
        │                                                 │
        │  ┌─────────────────────────────────────────┐   │
        │  │ Voice Management                        │   │
        │  │ - Voice list caching                    │   │
        │  │ - Voice metadata                        │   │
        │  └─────────────────────────────────────────┘   │
        │                                                 │
        │  ┌─────────────────────────────────────────┐   │
        │  │ Configuration Management                │   │
        │  │ - API key (encrypted)                   │   │
        │  │ - TTS parameters (stability, etc)       │   │
        │  │ - Voice preferences                     │   │
        │  └─────────────────────────────────────────┘   │
        │                                                 │
        │  ┌─────────────────────────────────────────┐   │
        │  │ Quota/Usage Tracking                    │   │
        │  │ - Character count per day               │   │
        │  │ - Monthly usage reporting               │   │
        │  └─────────────────────────────────────────┘   │
        └─────────────────────┬──────────────────────────┘
                              │
                  ┌───────────▼───────────┐
                  │  ElevenLabs API       │
                  │ (Cloud / Remote)      │
                  └───────────────────────┘
```

## Component Overview

### Core Library (`Core/`)
Shared functionality used by service and plugins:
- **Configuration Management**: Load/save config, encrypt API key
- **ElevenLabs API Client**: HTTP client for voice/synthesis endpoints
- **Audio Format Handling**: PCM, MP3, support across formats
- **Logging/Telemetry**: Structured logging, optional telemetry

### Service (`Service/`)
Local Windows service that handles all synthesis:
- **REST API**: HTTP endpoints on `localhost:11776`
- **IPC Interface**: Named pipes for high-performance access
- **Voice Caching**: In-memory voice list (refreshed periodically)
- **Audio Streaming**: Stream PCM audio to client
- **Resource Management**: Memory, bandwidth throttling
- **Quota Tracking**: Track usage per day/month

**Key Endpoints:**
```
GET    /api/voices              # List available voices
POST   /api/synthesize          # Synthesize text to audio
GET    /api/status              # Service health/status
POST   /api/config/reload       # Reload configuration
GET    /api/usage               # Usage statistics
```

### Plugins (`Plugins/`)

#### Calibre Plugin
- Integrates with Calibre's "Read Aloud" feature
- Auto-discovery of local service
- Configuration UI for voice selection
- Fallback to built-in TTS if service unavailable

#### NVDA Plugin
- Integrates with NVDA speech synthesizer API
- Provides voice list to NVDA
- Handles rate/volume adjustments
- Works with NVDA's existing UI

#### Windows.Media.SpeechSynthesis Provider
- Registers as a system speech synthesizer
- Available to any UWP/modern Windows app
- Voice list appears in Windows settings
- Seamless integration with new applications

#### Common Plugin Utilities (`Plugins/Common/`)
- Service discovery (find localhost service)
- HTTP client wrapper
- Configuration UI components
- Error handling/retries

### Installer (`Installer/`)
- Windows MSI installer
- Service installation with auto-start
- Plugin installation for Calibre, NVDA, etc.
- Configuration wizard (API key setup)
- Auto-update capability

## Data Flow Example: Calibre → ElevenLabs

```
1. User selects "Read Aloud" in Calibre
2. Calibre plugin discovers local service (localhost:11776)
3. Plugin queries service for available voices:
   GET /api/voices
   Response: [{"id": "1", "name": "Bella"}, ...]
4. User selects voice "Bella"
5. Plugin sends synthesis request:
   POST /api/synthesize
   {
     "text": "Chapter 1: The Beginning",
     "voice_id": "1",
     "rate": 1.0
   }
6. Service:
   - Loads config (API key)
   - Calls ElevenLabs API
   - Gets PCM audio stream
   - Returns audio to plugin
7. Calibre plugin streams audio to speakers
8. Service logs usage (characters, timestamp)
```

## Configuration

Service looks for `config.json` in:
- `%APPDATA%\ElevenLabsSpeechSynthesis\config.json`

```json
{
  "api_key": "sk_... (encrypted in file)",
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

## Security Model

1. **API Key Storage**: Encrypted at rest using DPAPI (Windows Data Protection)
2. **Network**: All communication via localhost (no external network listening)
3. **Permissions**: Service runs as LocalSystem, plugins run with user permissions
4. **Quota Limits**: Per-user API key limits (configured by user)
5. **Audit Logging**: All synthesis requests logged with timestamp/character count

## Technology Stack

- **Service**: C# .NET 6+ (Windows Service)
- **Plugins**: 
  - Calibre: Python (Calibre plugin format)
  - NVDA: Python (NVDA add-on format)
  - WinRT: C# (modern Windows API)
- **Core Library**: C# (shared assembly)
- **Installer**: WiX or NSIS

## Development Phases

### Phase 1: Core Service & REST API
- [ ] Service skeleton (Windows Service boilerplate)
- [ ] Configuration management (encrypted API key storage)
- [ ] ElevenLabs API client
- [ ] REST API endpoints
- [ ] Voice caching
- [ ] Logging

### Phase 2: Calibre Plugin
- [ ] Calibre plugin discovery
- [ ] Voice list integration
- [ ] Synthesis request handling
- [ ] Audio playback
- [ ] User configuration UI

### Phase 3: NVDA Plugin
- [ ] NVDA add-on structure
- [ ] Speech synthesizer API implementation
- [ ] Voice rate/volume adjustments
- [ ] Voice persistence

### Phase 4: Windows Media Speech Synthesizer Provider
- [ ] WinRT SpeechSynthesizer registration
- [ ] Voice provider interface
- [ ] Modern Windows app integration

### Phase 5: Installer & Deployment
- [ ] MSI installer creation
- [ ] Configuration wizard
- [ ] Auto-start service
- [ ] Plugin bundling

### Phase 6: Testing & Refinement
- [ ] Integration testing with Calibre, NVDA, Windows apps
- [ ] Performance optimization
- [ ] Error handling & recovery
- [ ] Documentation

## Future Extensions

- **Web UI**: Browser-based dashboard for configuration/usage tracking
- **Mobile Support**: WinRT APIs could extend to Windows Phone/Tablet
- **Other Applications**: Plugins for VLC, MPC-HC, other media players
- **Cloud Backup**: Optional cloud sync for configuration
- **Voice Cloning**: Support for custom voice models
- **Real-time Transcription**: Optional speech-to-text pipeline

## Comparison: Old vs New Architecture

| Aspect | SAPI5 (Legacy) | New Platform |
|--------|---|---|
| **Scope** | System-level voice | Local TTS service |
| **Target Apps** | SAPI5-aware only | Any application |
| **Configuration** | Per-installation | Once, system-wide |
| **Sustainability** | SAPI5 deprecated | Platform-agnostic |
| **Extensibility** | Limited | Plugin ecosystem |
| **User Control** | System admin | End user |
| **Quota Tracking** | None | Built-in |
| **Multi-app Support** | Through system voices | Native to architecture |
