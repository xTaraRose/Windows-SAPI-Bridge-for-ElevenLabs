using System;
using System.IO;
using Serilog;
using Serilog.Core;
using Serilog.Events;

namespace ElevenLabsSpeechSynthesis.Core
{
    /// <summary>
    /// Logging configuration for the platform.
    /// Ensures consistent logging across service and plugins.
    /// </summary>
    public static class LoggingSetup
    {
        private static readonly string LogDirectory =
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                        "ElevenLabsSpeechSynthesis");

        /// <summary>
        /// Initialize Serilog with file and console logging.
        /// </summary>
        public static void Initialize(string logLevel = "Information")
        {
            var level = logLevel.ToLower() switch
            {
                "debug" => LogEventLevel.Debug,
                "info" or "information" => LogEventLevel.Information,
                "warning" => LogEventLevel.Warning,
                "error" => LogEventLevel.Error,
                "fatal" => LogEventLevel.Fatal,
                _ => LogEventLevel.Information
            };

            if (!Directory.Exists(LogDirectory))
            {
                Directory.CreateDirectory(LogDirectory);
            }

            Log.Logger = new LoggerConfiguration()
                .MinimumLevel.Is(level)
                .WriteTo.File(
                    path: Path.Combine(LogDirectory, "service.log"),
                    rollingInterval: RollingInterval.Day,
                    retainedFileCountLimit: 14, // Keep 2 weeks of logs
                    outputTemplate: "[{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz}] [{Level:u3}] {Message:lj}{NewLine}{Exception}")
                .WriteTo.Console(
                    outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}")
                .Enrich.FromLogContext()
                .Enrich.WithProperty("Application", "ElevenLabsSpeechSynthesis")
                .CreateLogger();

            Log.Information("Logging initialized - Level: {LogLevel}", logLevel);
        }

        /// <summary>
        /// Shut down logging (flush pending logs).
        /// </summary>
        public static void Shutdown()
        {
            Log.CloseAndFlush();
        }

        /// <summary>
        /// Get the log directory path.
        /// </summary>
        public static string GetLogDirectory() => LogDirectory;
    }
}
