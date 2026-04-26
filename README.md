<a href="https://www.buymeacoffee.com/xTaraRose" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-purple.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a>

# Windows SAPI Bridge for ElevenLabs

> **Seamless ElevenLabs TTS — everywhere Windows speaks.**

---

## Why I built this

*by [@xTaraRose](https://github.com/xTaraRose)*

I was tired of trying to find different implementations to integrate ElevenLabs into different apps and always coming up short with nothing straightforward and simple to use.  Especially with using Calibre a lot — there was realistically nothing out there.

So I present to you the **Windows SAPI Bridge for ElevenLabs**.

It works across the board with anything that uses the Windows SAPI, allowing seamless use of the ElevenLabs TTS engine and resulting in a much better listening experience — no per-app setup, no hacks, no workarounds.  Install once, use everywhere.

---

## What it does

Windows TTS is built on the **SAPI5** (Speech API) standard.  Every voice on your system — including Microsoft's built-in ones — is just a COM object registered in the Windows registry.  Any application that uses SAPI for text-to-speech will automatically see and be able to use any registered voice.

This project:

1. Registers a lightweight Python COM server (`elevenlabs_engine.py`) as a SAPI5 engine.
2. Queries your ElevenLabs account and creates one SAPI voice token per voice.
3. Each token appears in Windows' voice list as `ElevenLabs - <Name>` — indistinguishable from a built-in voice.
4. When an app speaks, the engine streams raw PCM audio from ElevenLabs and hands it directly to SAPI, which plays it through your audio device.

**Works with any SAPI5-compatible application**, including (but not limited to):

- 📚 E-book readers (e.g. Calibre's Read Aloud)
- ♿ Screen readers and accessibility tools (e.g. NVDA with SAPI voices, Windows Narrator)
- 🗣️ Dedicated TTS players (e.g. Balabolka, TTSReader)
- 🏠 Home automation / custom scripts using the Windows Speech SDK
- 🎮 Games and applications with built-in narration
- Any other software that exposes a "voice selection" dropdown powered by Windows TTS

---

## Requirements

| Requirement | Notes |
|---|---|
| Windows 10 / 11 (64-bit) | 32-bit Windows is not supported |
| Python 3.8+ (64-bit) | [python.org](https://www.python.org/downloads/) — match the system bitness |
| ElevenLabs account | Free tier works; paid gives more monthly quota |
| Internet connection | Audio is streamed in real time |

---

## Installation

### 1 — Install Python dependencies

Open a **normal** (non-admin) Command Prompt and run:

```
pip install comtypes requests
```

### 2 — Add your ElevenLabs API key

Open `config.json` in any text editor and replace `YOUR_API_KEY_HERE` with your key:

```json
{
    "api_key": "sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    ...
}
```

Keep `config.json` in the **same folder** as the Python scripts.  The engine re-reads it on every Speak call, so changes take effect immediately without reinstalling.

### 3 — Run the installer as Administrator

Right-click **Command Prompt** → **Run as administrator**, then:

```
cd C:\path\to\windows-sapi-bridge-elevenlabs
python install_voices.py
```

Expected output:

```
Step 1 — Fetching your ElevenLabs voices
  Found 12 voice(s).

Step 2 — Registering engine CLSID
  Engine CLSID : {6C0A3A4E-8F2B-4E5D-A3C7-1B9F2E8D4A6C}
  LocalServer32: "C:\Python\pythonw.exe" "C:\...\elevenlabs_engine.py"

Step 3 — Registering voice tokens
  ✓  ElevenLabs - Rachel  [21m00Tcm4TlvDq8ikWAM]
  ✓  ElevenLabs - Adam    [pNInz6obpgDQGcFmaJgB]
  ...

✅  Done!  12 voice(s) registered.
```

### 4 — Select a voice in your application

Open any SAPI-compatible application and look for its voice selection — you'll find all your ElevenLabs voices listed as `ElevenLabs - <Name>`.  Select one and it just works.

> The very first sentence takes 1–2 seconds longer while Windows spins up the COM server in the background.  All subsequent speech streams smoothly.

---

## Uninstalling

```
python uninstall_voices.py
```

Run as Administrator.  This cleanly removes all SAPI registrations.  Restart any open SAPI applications afterwards.

---

## Updating your voice list

Added or removed voices in your ElevenLabs account?  Just re-run the installer:

```
python install_voices.py
```

It overwrites existing entries and adds any new ones.

---

## Configuration

All settings live in `config.json`.  Edit the file at any time — changes take effect immediately without re-running the installer.

### Voice quality

| Key | Default | Description |
|---|---|---|
| `model_id` | `eleven_multilingual_v2` | TTS model.  `eleven_turbo_v2` is faster with slightly lower quality. |
| `stability` | `0.5` | `0.0` = more expressive / variable &nbsp; `1.0` = very consistent |
| `similarity_boost` | `0.75` | How closely to match the original voice character |
| `style` | `0.0` | Style exaggeration `0`–`1`.  Higher = more dramatic; costs a little more quota. |
| `use_speaker_boost` | `true` | Subtle quality enhancement.  Disable if you hear audio artefacts. |

### Speed control

| Key | Default | Description |
|---|---|---|
| `speed` | `1.0` | Baseline playback speed.  Range: `0.5` (half speed) → `2.0` (double speed). |
| `sapi_rate_scaling` | `true` | When `true`, the app's own rate/speed slider is also honoured (stacks on top of `speed`). |

**How speed stacking works:**
SAPI reports rate as an integer from `−10` (slowest) to `+10` (fastest).  With `sapi_rate_scaling` enabled, each unit adds or subtracts **5 %** of the baseline speed.  So if your `speed` is `1.0` and the app sets rate to `+4`, the final speed sent to ElevenLabs is `1.0 × 1.20 = 1.20`.

Set `sapi_rate_scaling` to `false` to ignore the app's rate control and rely solely on the `speed` value — useful when an app sends a non-zero default rate that you want to override.

**Examples:**

```json
// Normal speed, ignore the app's rate slider
{ "speed": 1.0, "sapi_rate_scaling": false }

// 20% faster baseline, but still let the app fine-tune
{ "speed": 1.2, "sapi_rate_scaling": true }

// Slow reader mode
{ "speed": 0.8, "sapi_rate_scaling": false }
```

---

## Troubleshooting

### Voices don't appear in the application

- Confirm the installer was run **as Administrator**.
- Restart the application after installing.
- Open **Registry Editor** (`regedit`) and verify that
  `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens` contains keys starting with `ElevenLabs_`.

### No audio / silent playback

Check the log at `%APPDATA%\ElevenLabsSAPI\engine.log` for error details.

Common causes:

| Symptom in log | Fix |
|---|---|
| `HTTP 401` | Your API key is wrong or expired — update `config.json` |
| `HTTP 429` | Monthly quota reached — upgrade ElevenLabs plan or wait for reset |
| `ModuleNotFoundError: comtypes` | Run `pip install comtypes requests` |
| Python path changed | Re-run `install_voices.py` to update the registry entry |

### Audio plays but the wrong text is spoken (garbled / skipped words)

This usually means the `SPVTEXTFRAG` struct offsets differ from expectations (a rare SAPI version mismatch).  In the log, look for the line that starts `Speaking:` — does it show the correct text?  If not, please open an issue and include the `SPVSTATE size` and `SPVTEXTFRAG size` values printed at startup.

### 32-bit Python warning

Install the **64-bit** Python distribution from [python.org](https://www.python.org/downloads/) and re-run the installer.

---

## How the speed system works (technical detail)

```
User config  ──► speed (0.5 – 2.0, default 1.0)
                        │
                        │  if sapi_rate_scaling = true
                        ▼
SAPI app rate ──► rate_adj (-10 to +10)
                        │  multiplier = 1.0 + rate_adj × 0.05
                        │
                        ▼
              final = speed × multiplier   (clamped to 0.5 – 2.0)
                        │
                        ▼
              ElevenLabs API  { "speed": final }
```

---

## Privacy

Text passed to Windows SAPI is forwarded to the ElevenLabs API over HTTPS.
ElevenLabs' privacy policy applies: <https://elevenlabs.io/privacy>

---

## Contributing

Pull requests and issues are welcome.  If you find an application where the
bridge doesn't work, please open an issue with the application name and version
and the relevant lines from `engine.log`.

---

## Licence

MIT — see `LICENSE` for details.

---

*Made with frustration and determination by [@xTaraRose](https://github.com/xTaraRose)*


---

<a href="https://www.buymeacoffee.com/xTaraRose" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-purple.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a>
