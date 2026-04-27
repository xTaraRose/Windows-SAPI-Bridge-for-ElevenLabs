using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Serilog;
using ElevenLabsSpeechSynthesis.Core;

namespace ElevenLabsSpeechSynthesis.Service
{
    /// <summary>
    /// Core service handling text-to-speech synthesis requests.
    /// Manages voice caching, API client, and usage tracking.
    /// </summary>
    public class SynthesisService
    {
        private readonly Configuration _config;
        private readonly ElevenLabsApiClient? _apiClient;
        private List<Voice>? _cachedVoices;

        public SynthesisService()
        {
            _config = Configuration.Load();

            if (string.IsNullOrEmpty(_config.ApiKey))
            {
                Log.Warning("No API key configured. Synthesis will fail until configured.");
                _apiClient = null;
            }
            else
            {
                _apiClient = new ElevenLabsApiClient(_config.ApiKey, _config.VoiceCacheTtlHours);
            }
        }

        /// <summary>
        /// Get available voices, from cache or API.
        /// </summary>
        public async Task<List<Voice>> GetVoicesAsync()
        {
            if (_apiClient == null)
            {
                Log.Warning("API client not initialized (missing API key)");
                return new List<Voice>();
            }

            try
            {
                var voices = await _apiClient.GetVoicesAsync(_config.CacheVoices == false);
                _cachedVoices = voices;
                return voices;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to get voices");
                return _cachedVoices ?? new List<Voice>();
            }
        }

        /// <summary>
        /// Synthesize text to audio.
        /// </summary>
        public async Task<SynthesisResult> SynthesizeAsync(SynthesisRequest request)
        {
            if (_apiClient == null)
            {
                return new SynthesisResult
                {
                    Success = false,
                    Error = "API client not initialized - API key not configured"
                };
            }

            if (string.IsNullOrWhiteSpace(request.Text))
            {
                return new SynthesisResult
                {
                    Success = false,
                    Error = "Text cannot be empty"
                };
            }

            try
            {
                Log.Information("Synthesizing {CharCount} characters with voice {VoiceId}",
                    request.Text.Length, request.VoiceId);

                var audioBytes = await _apiClient.SynthesizeAsync(
                    request.Text,
                    request.VoiceId,
                    request.Stability ?? _config.Stability,
                    request.SimilarityBoost ?? _config.SimilarityBoost,
                    request.Style ?? _config.Style,
                    request.UseSpeakerBoost ?? _config.UseSpeakerBoost);

                if (_config.EnableUsageTracking)
                {
                    TrackUsage(request.Text);
                }

                return new SynthesisResult
                {
                    Success = true,
                    Audio = audioBytes,
                    CharacterCount = request.Text.Length
                };
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Synthesis failed");
                return new SynthesisResult
                {
                    Success = false,
                    Error = ex.Message
                };
            }
        }

        /// <summary>
        /// Get subscription information and usage.
        /// </summary>
        public async Task<UsageInfo?> GetUsageAsync()
        {
            if (_apiClient == null) return null;

            try
            {
                var subInfo = await _apiClient.GetSubscriptionInfoAsync();
                if (subInfo == null) return null;

                return new UsageInfo
                {
                    CharactersUsed = subInfo.CharacterCount,
                    CharacterLimit = subInfo.CharacterLimit,
                    CharactersRemaining = subInfo.CharacterLimit - subInfo.CharacterCount,
                    Tier = subInfo.Tier,
                    PercentageUsed = (float)subInfo.CharacterCount / subInfo.CharacterLimit * 100f
                };
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to get usage info");
                return null;
            }
        }

        /// <summary>
        /// Track usage for this request (for future analytics).
        /// </summary>
        private void TrackUsage(string text)
        {
            // TODO: Implement usage tracking to database or file
            Log.Debug("Usage tracked: {CharCount} characters at {Timestamp}",
                text.Length, DateTime.UtcNow);
        }

        public void Dispose()
        {
            _apiClient?.Dispose();
        }
    }

    /// <summary>
    /// Request for text synthesis.
    /// </summary>
    public class SynthesisRequest
    {
        public string Text { get; set; } = string.Empty;
        public string VoiceId { get; set; } = string.Empty;
        public float? Stability { get; set; }
        public float? SimilarityBoost { get; set; }
        public int? Style { get; set; }
        public bool? UseSpeakerBoost { get; set; }
    }

    /// <summary>
    /// Result of a synthesis request.
    /// </summary>
    public class SynthesisResult
    {
        public bool Success { get; set; }
        public byte[]? Audio { get; set; }
        public int CharacterCount { get; set; }
        public string? Error { get; set; }
    }

    /// <summary>
    /// User usage information.
    /// </summary>
    public class UsageInfo
    {
        public int CharactersUsed { get; set; }
        public int CharacterLimit { get; set; }
        public int CharactersRemaining { get; set; }
        public string Tier { get; set; } = string.Empty;
        public float PercentageUsed { get; set; }
    }
}
