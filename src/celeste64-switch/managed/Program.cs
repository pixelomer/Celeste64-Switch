using System.Globalization;
namespace Celeste64;
class Program
{
    public static void Main(string[] args)
    {
        Console.WriteLine("CELESTE64_SWITCH BOOT 1.1.1 A1 silent");
        CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
        CultureInfo.DefaultThreadCurrentUICulture = CultureInfo.InvariantCulture;
        // Native entry point creates SD directories before entering Mono.
        try { App.Run<Game>(Game.GamePath, 1280, 720); }
        catch (Exception e)
        {
            Console.WriteLine("CELESTE64_SWITCH ERROR " + e.GetType().FullName + ": " + e.Message);
            Console.WriteLine(e.ToString());
            try { File.WriteAllText("sdmc:/switch/celeste64/ErrorLog.txt", e.ToString()); } catch { }
        }
        Console.WriteLine("CELESTE64_SWITCH EXIT");
    }
}
