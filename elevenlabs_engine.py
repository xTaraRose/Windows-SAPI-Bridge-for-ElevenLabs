"""
Windows SAPI Bridge for ElevenLabs — COM Engine
================================================
Implements ISpTTSEngine and ISpObjectWithToken so any SAPI5-compatible
application on Windows can route text through ElevenLabs TTS.

This process is launched automatically by Windows COM when a SAPI application
requests one of the registered ElevenLabs voices.  Do NOT run it manually.

Logs: %APPDATA%\ElevenLabsSAPI\engine.log
"""

import sys
import os
import json
import ctypes
import ctypes.wintypes
import logging
import requests

# ─── Logging ──────────────────────────────────────────────────────────────────

_appdata  = os.environ.get('APPDATA', os.path.expanduser('~'))
_log_dir  = os.path.join(_appdata, 'ElevenLabsSAPI')
os.makedirs(_log_dir, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(_log_dir, 'engine.log'),
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
log = logging.getLogger('elevenlabs_sapi')
log.info('Engine module loading (pid=%d)', os.getpid())

# ─── Config ───────────────────────────────────────────────────────────────────

_script_dir  = os.path.dirname(os.path.abspath(__file__))
_config_path = os.path.join(_script_dir, 'config.json')

_DEFAULT_CONFIG = {
    'api_key':            '',
    'model_id':           'eleven_multilingual_v2',
    'stability':          0.5,
    'similarity_boost':   0.75,
    'style':              0.0,
    'use_speaker_boost':  True,
    'speed':              1.0,
    'sapi_rate_scaling':  True,
}


def load_config() -> dict:
    try:
        with open(_config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cfg = dict(_DEFAULT_CONFIG)
        cfg.update(data)
        return cfg
    except Exception as exc:
        log.error('Failed to load config.json: %s', exc)
        return dict(_DEFAULT_CONFIG)


# ─── Speed helpers ─────────────────────────────────────────────────────────────
#
# SAPI passes rate as an integer [-10, +10] via SPVSTATE.RateAdj.
#   -10 = slowest,  0 = normal,  +10 = fastest
# Each unit maps to a 5% speed change, applied on top of the config baseline.
# Result is clamped to ElevenLabs' accepted range [0.5, 2.0].

_EL_SPEED_MIN = 0.5
_EL_SPEED_MAX = 2.0


def sapi_rate_to_speed(base_speed: float, rate_adj: int) -> float:
    rate_adj   = max(-10, min(10, int(rate_adj)))
    multiplier = 1.0 + rate_adj * 0.05
    speed      = base_speed * multiplier
    return max(_EL_SPEED_MIN, min(_EL_SPEED_MAX, speed))


# ─── COM / comtypes imports ───────────────────────────────────────────────────

import comtypes
import comtypes.server.localserver as localserver
from comtypes import GUID, IUnknown, HRESULT, STDMETHOD, CoClass

# ─── SAPI 5 GUIDs ─────────────────────────────────────────────────────────────

IID_ISpTTSEngine       = GUID('{A74D7C8E-4CC9-4FBE-8B0F-7BEBE35B4D22}')
IID_ISpObjectWithToken = GUID('{5B559F40-E952-11D2-BB91-00C04F8EE6C0}')
SPDFID_WaveFormatEx    = GUID('{C31ADBAE-527F-4FF5-A230-F62BB61FF70C}')
CLSID_ElevenLabsEngine = GUID('{6C0A3A4E-8F2B-4E5D-A3C7-1B9F2E8D4A6C}')

# ─── HRESULT constants ────────────────────────────────────────────────────────

S_OK          =  0
E_FAIL        = -2147467259
E_NOTIMPL     = -2147467263
E_OUTOFMEMORY = -2147024882

# ─── SPVES action flags ───────────────────────────────────────────────────────

SPVES_CONTINUE = 0
SPVES_ABORT    = 1
SPVES_SKIP     = 2

# ─── Audio constants ──────────────────────────────────────────────────────────

WAVE_FORMAT_PCM = 0x0001
SAMPLE_RATE     = 22050
CHANNELS        = 1
BITS_PER_SAMPLE = 16

# ─── COM heap ─────────────────────────────────────────────────────────────────

ctypes.windll.ole32.CoTaskMemAlloc.restype  = ctypes.c_void_p
ctypes.windll.ole32.CoTaskMemAlloc.argtypes = [ctypes.c_size_t]
ctypes.windll.ole32.CoTaskMemFree.restype   = None
ctypes.windll.ole32.CoTaskMemFree.argtypes  = [ctypes.c_void_p]

# ─── SAPI structures ──────────────────────────────────────────────────────────

class WAVEFORMATEX(ctypes.Structure):
    _fields_ = [
        ('wFormatTag',      ctypes.c_ushort),
        ('nChannels',       ctypes.c_ushort),
        ('nSamplesPerSec',  ctypes.c_ulong),
        ('nAvgBytesPerSec', ctypes.c_ulong),
        ('nBlockAlign',     ctypes.c_ushort),
        ('wBitsPerSample',  ctypes.c_ushort),
        ('cbSize',          ctypes.c_ushort),
    ]


class SPVPITCH(ctypes.Structure):
    _fields_ = [('MiddleAdj', ctypes.c_long), ('RangeAdj', ctypes.c_long)]


class SPCONTEXTREFERENCE(ctypes.Structure):
    _fields_ = [('pszCategory', ctypes.c_wchar_p), ('pszId', ctypes.c_wchar_p)]


class SPVSTATE(ctypes.Structure):
    _fields_ = [
        ('eAction',       ctypes.c_uint),
        ('LangID',        ctypes.c_ushort),
        ('wReserved',     ctypes.c_ushort),
        ('RateAdj',       ctypes.c_long),   # ← SAPI rate adjustment (-10 to +10)
        ('Volume',        ctypes.c_ushort),
        ('_pad1',         ctypes.c_ushort),
        ('PitchAdj',      SPVPITCH),
        ('SilenceMsecs',  ctypes.c_ulong),
        ('_pad2',         ctypes.c_ulong),
        ('pPhoneIds',     ctypes.c_void_p),
        ('ePartOfSpeech', ctypes.c_uint),
        ('_pad3',         ctypes.c_uint),
        ('Context',       SPCONTEXTREFERENCE),
    ]


class SPVTEXTFRAG(ctypes.Structure):
    _fields_ = [
        ('pNext',           ctypes.c_void_p),
        ('State',           SPVSTATE),
        ('pTextStart',      ctypes.c_void_p),
        ('ulTextLen',       ctypes.c_ulong),
        ('ulTextSrcOffset', ctypes.c_ulong),
    ]


log.debug(
    'Structure sizes: SPVSTATE=%d (expect 64), SPVTEXTFRAG=%d (expect 88)',
    ctypes.sizeof(SPVSTATE), ctypes.sizeof(SPVTEXTFRAG),
)


# ─── ISpTTSEngineSite vtable helpers ─────────────────────────────────────────

def _vtbl_fn(obj_ptr: int, idx: int, restype, *argtypes):
    vtbl   = ctypes.cast(obj_ptr, ctypes.POINTER(ctypes.c_void_p))[0]
    fn_ptr = ctypes.cast(vtbl,   ctypes.POINTER(ctypes.c_void_p))[idx]
    return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(fn_ptr)


def site_get_actions(site: int) -> int:
    try:
        return _vtbl_fn(site, 5, ctypes.c_ulong)(site)
    except Exception:
        log.exception('site_get_actions failed')
        return SPVES_CONTINUE


def site_write(site: int, data: bytes) -> bool:
    try:
        fn = _vtbl_fn(site, 6, HRESULT,
                      ctypes.c_void_p, ctypes.c_ulong,
                      ctypes.POINTER(ctypes.c_ulong))
        buf     = (ctypes.c_char * len(data)).from_buffer_copy(data)
        written = ctypes.c_ulong(0)
        return fn(site, buf, len(data), ctypes.byref(written)) >= 0
    except Exception:
        log.exception('site_write failed')
        return False


def token_get_string_value(token: int, key_name: str) -> str:
    try:
        fn = _vtbl_fn(token, 5, HRESULT,
                      ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_wchar_p))
        result = ctypes.c_wchar_p(None)
        hr     = fn(token, key_name, ctypes.byref(result))
        if hr >= 0 and result.value:
            val = result.value
            ctypes.windll.ole32.CoTaskMemFree(result)
            return val
        return ''
    except Exception:
        log.exception('token_get_string_value failed')
        return ''


# ─── ElevenLabs API ───────────────────────────────────────────────────────────

_BASE = 'https://api.elevenlabs.io/v1'


def stream_pcm(api_key: str, voice_id: str, text: str,
               model_id: str, stability: float, similarity_boost: float,
               style: float, use_speaker_boost: bool, speed: float):
    """Stream raw PCM (pcm_22050) from ElevenLabs, yielding byte chunks."""
    url  = f'{_BASE}/text-to-speech/{voice_id}/stream'
    hdrs = {'xi-api-key': api_key, 'Content-Type': 'application/json'}
    body = {
        'text':     text,
        'model_id': model_id,
        'voice_settings': {
            'stability':         stability,
            'similarity_boost':  similarity_boost,
            'style':             style,
            'use_speaker_boost': use_speaker_boost,
        },
        'output_format': 'pcm_22050',
        'speed':         round(speed, 3),
    }
    log.debug('EL request: voice=%s speed=%.2f text_len=%d', voice_id, speed, len(text))
    resp = requests.post(url, json=body, headers=hdrs, stream=True, timeout=60)
    resp.raise_for_status()
    for chunk in resp.iter_content(chunk_size=4096):
        if chunk:
            yield chunk


# ─── COM interface declarations ───────────────────────────────────────────────

class ISpObjectWithToken(IUnknown):
    _iid_     = IID_ISpObjectWithToken
    _methods_ = [
        STDMETHOD(HRESULT, 'SetObjectToken', [ctypes.c_void_p]),
        STDMETHOD(HRESULT, 'GetObjectToken',  [ctypes.c_void_p]),
    ]


class ISpTTSEngine(IUnknown):
    _iid_     = IID_ISpTTSEngine
    _methods_ = [
        STDMETHOD(HRESULT, 'Speak', [
            ctypes.c_ulong, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ]),
        STDMETHOD(HRESULT, 'GetOutputFormat', [
            ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p,
        ]),
    ]


# ─── Engine implementation ────────────────────────────────────────────────────

class ElevenLabsTTSEngine(CoClass):
    _reg_clsid_      = CLSID_ElevenLabsEngine
    _reg_clsctx_     = 5  # CLSCTX_LOCAL_SERVER
    _reg_desc_       = 'ElevenLabs TTS Engine'
    _reg_progid_     = 'ElevenLabsSAPI.Engine'
    _com_interfaces_ = [ISpTTSEngine, ISpObjectWithToken]

    def __init__(self):
        self._voice_id: str  = ''
        self._config:   dict = {}
        log.info('ElevenLabsTTSEngine instance created')

    def QueryInterface(self, riid, ppvObj):
        from comtypes import GUID
        log.info('QueryInterface: riid=%s', riid)
        return super().QueryInterface(riid, ppvObj)

    def SetObjectToken(self, pToken):
        log.info('SetObjectToken() called with pToken=0x%X', pToken or 0)
        if not pToken:
            log.info('SetObjectToken: NULL token, returning S_OK')
            return S_OK
        try:
            self._config   = load_config()
            self._voice_id = token_get_string_value(pToken, 'ElevenLabsVoiceId')
            log.info('SetObjectToken: Successfully set voice_id=%r', self._voice_id)
            if not self._voice_id:
                log.warning('SetObjectToken: Warning - voice_id is empty!')
        except Exception:
            log.exception('SetObjectToken failed')
        return S_OK

    def GetObjectToken(self, ppToken):
        return E_NOTIMPL

    def GetOutputFormat(self, pTargetFmtId, pTargetWaveFormatEx,
                        pDesiredFormatId, ppCoMemDesiredWaveFormatEx):
        log.info('GetOutputFormat() called')
        try:
            if pDesiredFormatId:
                ctypes.memmove(pDesiredFormatId, bytes(SPDFID_WaveFormatEx), 16)

            wfx_ptr = ctypes.windll.ole32.CoTaskMemAlloc(ctypes.sizeof(WAVEFORMATEX))
            if not wfx_ptr:
                return E_OUTOFMEMORY

            wfx = WAVEFORMATEX.from_address(wfx_ptr)
            wfx.wFormatTag      = WAVE_FORMAT_PCM
            wfx.nChannels       = CHANNELS
            wfx.nSamplesPerSec  = SAMPLE_RATE
            wfx.wBitsPerSample  = BITS_PER_SAMPLE
            wfx.nBlockAlign     = CHANNELS * BITS_PER_SAMPLE // 8
            wfx.nAvgBytesPerSec = SAMPLE_RATE * wfx.nBlockAlign
            wfx.cbSize          = 0

            if ppCoMemDesiredWaveFormatEx:
                ctypes.c_void_p.from_address(ppCoMemDesiredWaveFormatEx).value = wfx_ptr

            return S_OK
        except Exception:
            log.exception('GetOutputFormat failed')
            return E_FAIL

    def Speak(self, dwSpeakFlags, rguidFormatId, pWaveFormatEx,
              pTextFragList, pOutputSite):
        """
        Walk SPVTEXTFRAG list → resolve speed → stream ElevenLabs PCM → SAPI.
        """
        log.info('Speak() called! (flags=0x%X, voice_id=%r)', dwSpeakFlags, self._voice_id)
        try:
            if not self._voice_id:
                log.error('Speak: no voice ID')
                return E_FAIL
            if not pOutputSite:
                log.error('Speak: NULL output site')
                return E_FAIL

            # ── Collect text + SAPI rate ──────────────────────────────────
            parts    = []
            rate_adj = 0
            frag_ptr = pTextFragList

            while frag_ptr:
                try:
                    frag = SPVTEXTFRAG.from_address(frag_ptr)
                except Exception:
                    log.warning('Cannot read SPVTEXTFRAG at 0x%X', frag_ptr)
                    break

                if not parts:
                    rate_adj = frag.State.RateAdj

                if frag.pTextStart and frag.ulTextLen > 0:
                    try:
                        buf = (ctypes.c_wchar * frag.ulTextLen).from_address(
                                  frag.pTextStart)
                        parts.append(''.join(buf))
                    except Exception:
                        log.warning('Cannot read text at 0x%X', frag.pTextStart)

                frag_ptr = frag.pNext

            text = ''.join(parts).strip()
            if not text:
                return S_OK

            log.info('Speak: %d chars, rate_adj=%+d  %r…',
                     len(text), rate_adj, text[:60])

            # ── Resolve final speed ───────────────────────────────────────
            cfg        = self._config
            base_speed = float(cfg.get('speed', 1.0))
            if cfg.get('sapi_rate_scaling', True):
                final_speed = sapi_rate_to_speed(base_speed, rate_adj)
            else:
                final_speed = max(_EL_SPEED_MIN, min(_EL_SPEED_MAX, base_speed))

            log.debug('Speed: base=%.2f sapi_adj=%+d final=%.2f',
                      base_speed, rate_adj, final_speed)

            # ── Stream PCM → SAPI ─────────────────────────────────────────
            site   = int(pOutputSite)
            chunks = stream_pcm(
                api_key          = cfg.get('api_key', ''),
                voice_id         = self._voice_id,
                text             = text,
                model_id         = cfg.get('model_id', 'eleven_multilingual_v2'),
                stability        = cfg.get('stability', 0.5),
                similarity_boost = cfg.get('similarity_boost', 0.75),
                style            = cfg.get('style', 0.0),
                use_speaker_boost= cfg.get('use_speaker_boost', True),
                speed            = final_speed,
            )

            for chunk in chunks:
                if site_get_actions(site) & SPVES_ABORT:
                    log.info('Speak: aborted by SAPI')
                    return S_OK
                if not site_write(site, chunk):
                    log.warning('Speak: site_write failed')
                    break

            log.debug('Speak: done')
            return S_OK

        except requests.HTTPError as exc:
            log.error('ElevenLabs HTTP error: %s', exc)
            return E_FAIL
        except requests.RequestException as exc:
            log.error('Network error: %s', exc)
            return E_FAIL
        except Exception:
            log.exception('Speak: unexpected error')
            return E_FAIL


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    comtypes.CoInitialize()
    log.info('COM LocalServer32 starting…')
    try:
        # Try newer comtypes API (run) first, fall back to older API (serve) if needed
        if hasattr(localserver, 'run'):
            localserver.run([ElevenLabsTTSEngine])
        else:
            localserver.serve([ElevenLabsTTSEngine])
    except Exception:
        log.exception('Fatal error in COM server loop')
        sys.exit(1)
    finally:
        comtypes.CoUninitialize()
        log.info('COM LocalServer32 exited cleanly.')
