using Xunit;
using ElevenLabsTTSEngine;

namespace ElevenLabsTTSEngine.Tests
{
    public class EngineTests
    {
        [Fact]
        public void Constructor_CreateInstance_Success()
        {
            // Arrange & Act
            var engine = new ElevenLabsTTSEngine();

            // Assert
            Assert.NotNull(engine);
        }

        [Fact]
        public async void InitializeAsync_WithValidConfig_Succeeds()
        {
            // Arrange
            var engine = new ElevenLabsTTSEngine();
            var configPath = "config.json"; // TODO: Use test fixture config

            // Act & Assert
            // TODO: Create test configuration and verify initialization
            await engine.InitializeAsync(configPath);
        }

        [Fact]
        public async void SynthesizeAsync_WithValidInput_ReturnsAudio()
        {
            // Arrange
            var engine = new ElevenLabsTTSEngine();
            var text = "Hello, this is a test.";
            var voiceId = "test-voice-id";

            // Act & Assert
            // TODO: Mock ElevenLabs API and verify synthesis
            var result = await engine.SynthesizeAsync(text, voiceId);
            Assert.NotNull(result);
        }
    }
}
