using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Serilog;
using ElevenLabsSpeechSynthesis.Plugins.Common;

namespace ElevenLabsSpeechSynthesis.Plugins.WindowsMedia
{
    /// <summary>
    /// Windows.Media.SpeechSynthesis provider that integrates ElevenLabs voices.
    /// This allows modern Windows applications to use ElevenLabs voices.
    /// </summary>
    public class VoiceProvider
    {
        private readonly ServiceDiscovery _serviceDiscovery;

        public VoiceProvider()
        {
            _serviceDiscovery = new ServiceDiscovery();
        }

        /// <summary>
        /// Get available voices from the synthesis service.
        /// </summary>
        public async Task<List<VoiceInfo>> GetAvailableVoicesAsync()
        {
            var isAvailable = await _serviceDiscovery.IsServiceAvailableAsync();
            if (!isAvailable)
            {
                Log.Warning("Synthesis service is not available");
                return new List<VoiceInfo>();
            }

            try
            {
                // TODO: Call service to get voices
                // var voices = await _serviceDiscovery.GetAsync<List<Voice>>("/voices");

                var voiceInfos = new List<VoiceInfo>();
                // TODO: Convert Voice objects to VoiceInfo for WinRT API

                return voiceInfos;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to get available voices");
                return new List<VoiceInfo>();
            }
        }

        /// <summary>
        /// Synthesize text using ElevenLabs.
        /// </summary>
        public async Task<byte[]> SynthesizeAsync(string text, string voiceId)
        {
            try
            {
                var isAvailable = await _serviceDiscovery.IsServiceAvailableAsync();
                if (!isAvailable)
                {
                    Log.Warning("Synthesis service is not available");
                    return Array.Empty<byte>();
                }

                // TODO: Call service to synthesize
                // var request = new { text, voiceId };
                // var result = await _serviceDiscovery.PostAsync<SynthesisRequest, byte[]>("/synthesize", request);

                return Array.Empty<byte>();
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Synthesis failed");
                return Array.Empty<byte>();
            }
        }
    }

    /// <summary>
    /// Voice metadata for WinRT API.
    /// </summary>
    public class VoiceInfo
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Language { get; set; } = "en-US";
        public string Gender { get; set; } = "Unknown";
        public string Description { get; set; } = string.Empty;
    }
}
