using System;
using System.IO;
using System.Text;
using Newtonsoft.Json;
using Serilog;

namespace ElevenLabsSpeechSynthesis.Core
{
    /// <summary>
    /// Configuration management for ElevenLabs Speech Synthesis Platform.
    /// Handles encrypted API key storage, TTS parameters, and user preferences.
    /// </summary>
    public class Configuration
    {
        private static readonly string ConfigDirectory =
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                        "ElevenLabsSpeechSynthesis");

        private static readonly string ConfigFile = Path.Combine(ConfigDirectory, "config.json");

        public string? ApiKey { get; set; }
        public float Stability { get; set; } = 0.5f;
        public float SimilarityBoost { get; set; } = 0.75f;
        public int Style { get; set; } = 0;
        public bool UseSpeakerBoost { get; set; } = false;
        public float Speed { get; set; } = 1.0f;
        public bool CacheVoices { get; set; } = true;
        public int VoiceCacheTtlHours { get; set; } = 24;
        public bool EnableUsageTracking { get; set; } = true;
        public int Port { get; set; } = 11776;
        public string LogLevel { get; set; } = "info";

        /// <summary>
        /// Load configuration from file. Creates default config if file doesn't exist.
        /// </summary>
        public static Configuration Load()
        {
            try
            {
                if (!Directory.Exists(ConfigDirectory))
                {
                    Directory.CreateDirectory(ConfigDirectory);
                    Log.Information("Created configuration directory: {ConfigDir}", ConfigDirectory);
                }

                if (File.Exists(ConfigFile))
                {
                    var json = File.ReadAllText(ConfigFile, Encoding.UTF8);
                    var config = JsonConvert.DeserializeObject<Configuration>(json);

                    if (config?.ApiKey != null)
                    {
                        config.ApiKey = DecryptApiKey(config.ApiKey);
                    }

                    Log.Information("Configuration loaded from {ConfigFile}", ConfigFile);
                    return config ?? new Configuration();
                }
                else
                {
                    Log.Warning("Configuration file not found at {ConfigFile}. Using defaults.", ConfigFile);
                    return new Configuration();
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to load configuration from {ConfigFile}", ConfigFile);
                return new Configuration();
            }
        }

        /// <summary>
        /// Save configuration to file. API key is encrypted before storage.
        /// </summary>
        public void Save()
        {
            try
            {
                if (!Directory.Exists(ConfigDirectory))
                {
                    Directory.CreateDirectory(ConfigDirectory);
                }

                var configCopy = (Configuration)MemberwiseClone();

                if (!string.IsNullOrEmpty(configCopy.ApiKey))
                {
                    configCopy.ApiKey = EncryptApiKey(configCopy.ApiKey);
                }

                var json = JsonConvert.SerializeObject(configCopy, Formatting.Indented);
                File.WriteAllText(ConfigFile, json, Encoding.UTF8);

                Log.Information("Configuration saved to {ConfigFile}", ConfigFile);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to save configuration to {ConfigFile}", ConfigFile);
            }
        }

        /// <summary>
        /// Encrypt API key using Windows DPAPI (Data Protection API).
        /// </summary>
        private static string EncryptApiKey(string plainKey)
        {
            try
            {
                var keyBytes = Encoding.UTF8.GetBytes(plainKey);
                var encryptedBytes = System.Security.Cryptography.ProtectedData.Protect(
                    keyBytes,
                    null,
                    System.Security.Cryptography.DataProtectionScope.CurrentUser);

                return Convert.ToBase64String(encryptedBytes);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to encrypt API key");
                return plainKey; // Fallback: store unencrypted (not ideal)
            }
        }

        /// <summary>
        /// Decrypt API key using Windows DPAPI.
        /// </summary>
        private static string DecryptApiKey(string encryptedKey)
        {
            try
            {
                var encryptedBytes = Convert.FromBase64String(encryptedKey);
                var decryptedBytes = System.Security.Cryptography.ProtectedData.Unprotect(
                    encryptedBytes,
                    null,
                    System.Security.Cryptography.DataProtectionScope.CurrentUser);

                return Encoding.UTF8.GetString(decryptedBytes);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to decrypt API key");
                return encryptedKey; // Return encrypted if decryption fails
            }
        }

        /// <summary>
        /// Validate that required configuration is present.
        /// </summary>
        public bool IsValid()
        {
            return !string.IsNullOrEmpty(ApiKey);
        }

        /// <summary>
        /// Get the configuration file path (for debugging/reference).
        /// </summary>
        public static string GetConfigFilePath() => ConfigFile;
    }
}
