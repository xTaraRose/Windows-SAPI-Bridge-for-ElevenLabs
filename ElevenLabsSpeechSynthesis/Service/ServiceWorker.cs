using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Serilog;

namespace ElevenLabsSpeechSynthesis.Service
{
    /// <summary>
    /// Windows Service worker that manages the service lifecycle.
    /// TODO: Implement REST API server to listen for synthesis requests.
    /// </summary>
    public class ServiceWorker : BackgroundService
    {
        private readonly SynthesisService _synthesisService;

        public ServiceWorker(SynthesisService synthesisService)
        {
            _synthesisService = synthesisService ?? throw new ArgumentNullException(nameof(synthesisService));
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            Log.Information("Service worker started");

            try
            {
                // TODO: Start REST API server
                // var apiServer = new RestApiServer(_synthesisService, port: 11776);
                // await apiServer.StartAsync(stoppingToken);

                // For now, just keep the service alive
                while (!stoppingToken.IsCancellationRequested)
                {
                    await Task.Delay(1000, stoppingToken);
                }
            }
            catch (OperationCanceledException)
            {
                Log.Information("Service worker cancelled");
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Service worker encountered an error");
            }
        }

        public override async Task StopAsync(CancellationToken cancellationToken)
        {
            Log.Information("Service worker stopping");

            // TODO: Shutdown REST API server
            // apiServer?.Stop();

            await base.StopAsync(cancellationToken);
            _synthesisService.Dispose();
        }
    }
}
