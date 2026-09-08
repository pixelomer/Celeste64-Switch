using System.Runtime.InteropServices;
namespace Celeste64;

// All FMOD callbacks remain native. Timeline markers are dispatched on the game thread.
public static unsafe class Audio
{
    private static readonly Dictionary<IntPtr, Action> callbacks = new();
    private static readonly List<IntPtr> expired = new();
    private static bool initialized;
    private static int frame;
    public static void Init()
    {
        int result = Native.Init();
        if (result != 0) { Native.Shutdown(); Check(result); }
        initialized = true;
        Log.Info("Switch FMOD 2.02.18 audio backend");
    }
    internal static void Check(int result)
    {
        if (result != 0) throw new InvalidOperationException($"Switch FMOD error {result}; see native audio log. FMOD libraries must be in sdmc:/switch/celeste64/fmod/.");
    }
    public static void Shutdown()
    {
        callbacks.Clear();
        if (initialized) { initialized = false; Check(Native.Shutdown()); }
    }
    public static void Load(string path)
    {
        Check(Native.Load(path));
#if SWITCH_AUDIO_VALIDATE
        foreach (string music in new[] { "event:/music/mus_lvl1", "event:/music/mus_lvl1_bside" })
        {
            var test = Play(music);
            if (!test) throw new InvalidOperationException("FMOD variant probe could not create " + music);
            test.Set("at_baddy", 0);
            test.Set("at_baddy", 1);
            test.Stop();
            Log.Info("C64_AUDIO PASS managed variant " + music);
        }
#endif
    }
    public static void Unload() { callbacks.Clear(); Check(Native.Unload()); }
    public static void SetListener(in Camera camera)
    {
        var a = new Attributes { Position = camera.Position, Forward = camera.Forward, Up = camera.Up };
        Check(Native.Listener(ref a));
    }
    public static void SetVCAVolume(string path, float volume) => Check(Native.VCA(path, volume));
    public static void StopBus(string path, bool immediate = false) => Check(Native.Bus(path, -1, immediate ? 1 : 0));
    public static void SetBusPaused(string path, bool paused) => Check(Native.Bus(path, paused ? 1 : 0, 0));
    public static AudioHandle Play(string path, Vec3? position = null, float volume = 1)
    {
        if (string.IsNullOrEmpty(path)) return default;
        Attributes a = At(position ?? default);
        int result = Native.Play(path, position.HasValue ? &a : null, volume, out var handle);
        if (result != 0) { Log.Warning($"FMOD play failed: {path} ({result})"); return default; }
        return new AudioHandle(handle, path);
    }
    internal static Attributes At(Vec3 position) => new() { Position = position, Forward = Vec3.UnitX, Up = Vec3.UnitZ };
    internal static void Watch(IntPtr handle, Action callback) { Check(Native.Watch(handle)); callbacks[handle] = callback; }
    public static void Update()
    {
        Check(Native.Update());
        IntPtr handle;
        while ((handle = Native.Marker()) != IntPtr.Zero)
            if (callbacks.TryGetValue(handle, out var callback)) callback();
        if (++frame % 120 == 0)
        {
            expired.Clear();
            foreach (var it in callbacks) if (Native.State(it.Key) < 0) expired.Add(it.Key);
            foreach (var key in expired) callbacks.Remove(key);
        }
    }
    [StructLayout(LayoutKind.Sequential)]
    internal struct Attributes { public Vec3 Position, Velocity, Forward, Up; }
    internal static class Native
    {
        private const string Lib = "__Internal";
        [DllImport(Lib, EntryPoint="C64AudioInit")] internal static extern int Init();
        [DllImport(Lib, EntryPoint="C64AudioShutdown")] internal static extern int Shutdown();
        [DllImport(Lib, EntryPoint="C64AudioUpdate")] internal static extern int Update();
        [DllImport(Lib, EntryPoint="C64AudioLoad")] internal static extern int Load([MarshalAs(UnmanagedType.LPUTF8Str)] string path);
        [DllImport(Lib, EntryPoint="C64AudioUnload")] internal static extern int Unload();
        [DllImport(Lib, EntryPoint="C64AudioPlay")] internal static extern int Play([MarshalAs(UnmanagedType.LPUTF8Str)] string path, Attributes* attributes, float volume, out IntPtr handle);
        [DllImport(Lib, EntryPoint="C64AudioState")] internal static extern int State(IntPtr handle);
        [DllImport(Lib, EntryPoint="C64AudioStop")] internal static extern int Stop(IntPtr handle);
        [DllImport(Lib, EntryPoint="C64AudioWatch")] internal static extern int Watch(IntPtr handle);
        [DllImport(Lib, EntryPoint="C64AudioMarker")] internal static extern IntPtr Marker();
        [DllImport(Lib, EntryPoint="C64AudioParameter")] internal static extern int Parameter(IntPtr handle, [MarshalAs(UnmanagedType.LPUTF8Str)] string name, float value);
        [DllImport(Lib, EntryPoint="C64AudioPosition")] internal static extern int Position(IntPtr handle, ref Attributes a, int set);
        [DllImport(Lib, EntryPoint="C64AudioVolume")] internal static extern int Volume(IntPtr handle, ref float volume, int set);
        [DllImport(Lib, EntryPoint="C64AudioListener")] internal static extern int Listener(ref Attributes a);
        [DllImport(Lib, EntryPoint="C64AudioVCA")] internal static extern int VCA([MarshalAs(UnmanagedType.LPUTF8Str)] string name, float value);
        [DllImport(Lib, EntryPoint="C64AudioBus")] internal static extern int Bus([MarshalAs(UnmanagedType.LPUTF8Str)] string name, int pause, int immediate);
    }
}
public readonly struct AudioHandle
{
    private readonly IntPtr handle;
    private readonly string? path;
    internal AudioHandle(IntPtr handle, string path) { this.handle = handle; this.path = path; }
    public string Path => path ?? "";
    // FMOD PLAYING = 0, STARTING = 3, matching upstream AudioHandle.
    public bool IsPlaying { get { int state = Audio.Native.State(handle); return state == 0 || state == 3; } }
    public Vec3 Position
    {
        get { Audio.Attributes a = default; Audio.Check(Audio.Native.Position(handle, ref a, 0)); return a.Position; }
        set { var a = Audio.At(value); Audio.Check(Audio.Native.Position(handle, ref a, 1)); }
    }
    public float Volume
    {
        get { float v = 0; Audio.Check(Audio.Native.Volume(handle, ref v, 0)); return v; }
        set { Audio.Check(Audio.Native.Volume(handle, ref value, 1)); }
    }
    // Upstream deliberately ignores parameter errors: variants such as the B-side
    // music do not define every parameter set by World.Update.
    public void Set(string parameter, float value) => Audio.Native.Parameter(handle, parameter, value);
    public void Stop() => Audio.Check(Audio.Native.Stop(handle));
    public void SetCallback(Action callback) { if (handle != IntPtr.Zero) Audio.Watch(handle, callback); }
    public static implicit operator bool(AudioHandle audio) => Audio.Native.State(audio.handle) >= 0;
}
