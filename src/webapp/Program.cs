using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using Microsoft.Extensions.DependencyInjection;
using SerendipityWebApp.Data;
using System;
using System.Net.Http;
using System.Threading.Tasks;

namespace SerendipityWebApp
{
    public class Program
    {
        public static async Task Main(string[] args)
        {
            var builder = WebAssemblyHostBuilder.CreateDefault(args);
            builder.RootComponents.Add<App>("App");

            builder.Services.AddScoped(sp => new HttpClient { BaseAddress = new Uri("http://localhost:7071/api/") });
            builder.Services.AddScoped<LoginState>();

            await builder.Build().RunAsync();
        }
    }
}
