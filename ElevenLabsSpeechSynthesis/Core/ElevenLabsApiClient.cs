using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Serilog;

namespace ElevenLabsSpeechSynthesis.Core
{
    /// <summary>
    /// HTTP client for ElevenLabs API communication.
    /// Handles voice fetching and text-to-speech synthesis.
    /// </summary>
    public class ElevenLabsApiClient
    {
        private const string BaseUrl = "https://api.elevenlabs.io/v1";
        private readonly string _apiKey;
        private readonly HttpClient _httpClient;
        private List<Voice>? _voiceCache;
        private DateTime _voiceCacheTime = DateTime.MinValue;
        private readonly TimeSpan _cacheExpiry;

        public ElevenLabsApiClient(string apiKey, int cacheTtlHours = 24)
        {
            _apiKey = apiKey ?? throw new ArgumentNullException(nameof(apiKey));
            _httpClient = new HttpClient();
            _cacheExpiry = TimeSpan.FromHours(cacheTtlHours);
        }

        /// <summary>
        /// Fetch available voices from ElevenLabs API.
        /// Results are cached to reduce API calls.
        /// </summary>
        public async Task<List<Voice>> GetVoicesAsync(bool forceRefresh = false)
        {
            if (!forceRefresh && _voiceCache != null &&
                DateTime.UtcNow - _voiceCacheTime < _cacheExpiry)
            {
                Log.Debug("Returning cached voices");
                return _voiceCache;
            }

            try
            {
                var url = $"{BaseUrl}/voices";
                var request = new HttpRequestMessage(HttpMethod.Get, url);
                request.Headers.Add("xi-api-key", _apiKey);

                var response = await _httpClient.SendAsync(request);
                response.EnsureSuccessStatusCode();

                var json = await response.Content.ReadAsStringAsync();
                var data = JsonConvert.DeserializeObject<dynamic>(json);

                var voices = new List<Voice>();
                if (data?.voices != null)
                {
                    foreach (var voiceData in data.voices)
                    {
                        voices.Add(new Voice
                        {
                            Id = voiceData.voice_id,
                            Name = voiceData.name,
                            PreviewUrl = voiceData.preview_url,
                            AccentEng = voiceData.accent,
                            Category = voiceData.category
                        });
                    }
                }

                _voiceCache = voices;
                _voiceCacheTime = DateTime.UtcNow;

                Log.Information("Fetched {VoiceCount} voices from ElevenLabs API", voices.Count);
                return voices;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to fetch voices from ElevenLabs API");
                return _voiceCache ?? new List<Voice>();
            }
        }

        /// <summary>
        /// Synthesize text using ElevenLabs API.
        /// Returns raw audio stream in specified format.
        /// </summary>
        public async Task<byte[]> SynthesizeAsync(
            string text,
            string voiceId,
            float stability = 0.5f,
            float similarityBoost = 0.75f,
            int style = 0,
            bool useSpeakerBoost = false)
        {
            try
            {
                var url = $"{BaseUrl}/text-to-speech/{voiceId}";
                var request = new HttpRequestMessage(HttpMethod.Post, url);
                request.Headers.Add("xi-api-key", _apiKey);

                var body = new
                {
                    text = text,
                    model_id = "eleven_monolingual_v1",
                    voice_settings = new
                    {
                        stability = stability,
                        similarity_boost = similarityBoost,
                        style = style,
                        use_speaker_boost = useSpeakerBoost
                    }
                };

                var jsonBody = JsonConvert.SerializeObject(body);
                request.Content = new StringContent(jsonBody, System.Text.Encoding.UTF8, "application/json");

                // Request PCM audio format (16-bit, 22050Hz)
                request.Headers.Add("Accept", "audio/mpeg");

                var response = await _httpClient.SendAsync(request);
                response.EnsureSuccessStatusCode();

                var audioBytes = await response.Content.ReadAsByteArrayAsync();

                Log.Debug("Successfully synthesized {CharCount} characters", text.Length);
                return audioBytes;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to synthesize text for voice {VoiceId}", voiceId);
                return Array.Empty<byte>();
            }
        }

        /// <summary>
        /// Get user subscription information (for quota tracking).
        /// </summary>
        public async Task<SubscriptionInfo?> GetSubscriptionInfoAsync()
        {
            try
            {
                var url = $"{BaseUrl}/user/subscription";
                var request = new HttpRequestMessage(HttpMethod.Get, url);
                request.Headers.Add("xi-api-key", _apiKey);

                var response = await _httpClient.SendAsync(request);
                response.EnsureSuccessStatusCode();

                var json = await response.Content.ReadAsStringAsync();
                var info = JsonConvert.DeserializeObject<SubscriptionInfo>(json);

                return info;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to fetch subscription info");
                return null;
            }
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }

    /// <summary>
    /// Represents a voice available on ElevenLabs.
    /// </summary>
    public class Voice
    {
        [JsonProperty("voice_id")]
        public string Id { get; set; } = string.Empty;

        [JsonProperty("name")]
        public string Name { get; set; } = string.Empty;

        [JsonProperty("preview_url")]
        public string? PreviewUrl { get; set; }

        [JsonProperty("accent")]
        public string? AccentEng { get; set; }

        [JsonProperty("category")]
        public string? Category { get; set; }
    }

    /// <summary>
    /// User subscription information from ElevenLabs API.
    /// </summary>
    public class SubscriptionInfo
    {
        [JsonProperty("character_count")]
        public int CharacterCount { get; set; }

        [JsonProperty("character_limit")]
        public int CharacterLimit { get; set; }

        [JsonProperty("can_use_professional_voice_consistency")]
        public bool CanUseProfessionalVoiceConsistency { get; set; }

        [JsonProperty("tier")]
        public string Tier { get; set; } = string.Empty;
    }
}
