using System.Runtime.InteropServices;

namespace Celeste64;

internal static class NativeAotEntryPoint
{
    // The Horizon launcher initializes services, rendering and audio imports
    // before entering managed code. Program.Main retains the FMOD shutdown path.
    [UnmanagedCallersOnly(EntryPoint = "C64ManagedMain")]
    public static void Run() => Program.Main(Array.Empty<string>());
}
