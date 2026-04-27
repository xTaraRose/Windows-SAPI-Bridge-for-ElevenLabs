using System;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ElevenLabsSpeechSynthesis.Core;
using Serilog;

namespace ElevenLabsSpeechSynthesis.Service
{
    class Program
    {
        static void Main(string[] args)
        {
            // Initialize logging before anything else
            var config = Configuration.Load();
            LoggingSetup.Initialize(config.LogLevel);

            Log.Information("ElevenLabs Speech Synthesis Service starting...");

            try
            {
                CreateHostBuilder(args).Build().Run();
            }
            catch (Exception ex)
            {
                Log.Fatal(ex, "Application terminated unexpectedly");
            }
            finally
            {
                LoggingSetup.Shutdown();
            }
        }

        static IHostBuilder CreateHostBuilder(string[] args) =>
            Host.CreateDefaultBuilder(args)
                .UseWindowsService()
                .UseSerilog()
                .ConfigureServices((context, services) =>
                {
                    services.AddSingleton<SynthesisService>();
                    services.AddHostedService<ServiceWorker>();
                });
    }
}
