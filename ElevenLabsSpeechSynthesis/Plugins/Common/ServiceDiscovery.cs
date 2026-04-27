using System;
using System.Net.Http;
using System.Threading.Tasks;
using Serilog;

namespace ElevenLabsSpeechSynthesis.Plugins.Common
{
    /// <summary>
    /// Service discovery utility for plugins to find and communicate with the local service.
    /// </summary>
    public class ServiceDiscovery
    {
        private const string DefaultBaseUrl = "http://localhost:11776";
        private readonly HttpClient _httpClient;
        private bool _serviceAvailable = false;

        public ServiceDiscovery()
        {
            _httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(5) };
        }

        /// <summary>
        /// Check if the synthesis service is available.
        /// </summary>
        public async Task<bool> IsServiceAvailableAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{DefaultBaseUrl}/api/status");
                _serviceAvailable = response.IsSuccessStatusCode;
                return _serviceAvailable;
            }
            catch (Exception ex)
            {
                Log.Debug(ex, "Service availability check failed");
                _serviceAvailable = false;
                return false;
            }
        }

        /// <summary>
        /// Get the service base URL.
        /// </summary>
        public string GetServiceUrl() => DefaultBaseUrl;

        /// <summary>
        /// Make a GET request to the service.
        /// </summary>
        public async Task<T?> GetAsync<T>(string endpoint)
        {
            try
            {
                var url = $"{DefaultBaseUrl}/api{endpoint}";
                var response = await _httpClient.GetAsync(url);
                response.EnsureSuccessStatusCode();

                var json = await response.Content.ReadAsStringAsync();
                // TODO: Deserialize JSON to T using Json library
                return default;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "GET request failed: {Endpoint}", endpoint);
                return default;
            }
        }

        /// <summary>
        /// Make a POST request to the service.
        /// </summary>
        public async Task<T?> PostAsync<TRequest, TResponse>(string endpoint, TRequest request)
            where TRequest : class
        {
            try
            {
                var url = $"{DefaultBaseUrl}/api{endpoint}";
                var json = System.Text.Json.JsonSerializer.Serialize(request);
                var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

                var response = await _httpClient.PostAsync(url, content);
                response.EnsureSuccessStatusCode();

                var responseJson = await response.Content.ReadAsStringAsync();
                // TODO: Deserialize JSON to TResponse using Json library
                return default;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "POST request failed: {Endpoint}", endpoint);
                return default;
            }
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }
}
