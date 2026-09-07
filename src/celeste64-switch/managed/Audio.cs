namespace Celeste64;

// Silent milestone backend. Timing is deliberately approximate (120 BPM),
// but beat-driven actors still advance when there is no audio device.
public static class Audio
{
    private static readonly List<AudioHandle.State> tracks = new();
    public static void Init() => Log.Info("Switch silent audio backend (120 BPM)");
    public static void Load(string path) { }
    public static void Unload() => tracks.Clear();
    public static void SetListener(in Camera camera) { }
    public static void SetVCAVolume(string path, float volume) { }
    public static void StopBus(string path, bool immediate = false) { }
    public static void SetBusPaused(string path, bool paused) { }
    public static AudioHandle Play(string path, Vec3? position = null, float volume = 1)
    {
        if (string.IsNullOrEmpty(path)) return default;
        var state = new AudioHandle.State { Path = path, Position = position ?? default, Volume = volume };
        return new AudioHandle(state);
    }
    internal static void Track(AudioHandle.State state)
    {
        if (!tracks.Contains(state)) tracks.Add(state);
    }
    public static void Update()
    {
        for (int i = tracks.Count - 1; i >= 0; i--)
        {
            var track = tracks[i];
            if (!track.Playing) { tracks.RemoveAt(i); continue; }
            track.Elapsed += Time.Delta;
            if (track.Elapsed >= 0.5f) { track.Elapsed %= 0.5f; track.Callback?.Invoke(); }
        }
    }
}
public readonly struct AudioHandle
{
    internal sealed class State
    {
        public string Path = "";
        public Vec3 Position;
        public float Volume = 1, Elapsed;
        public bool Playing = true;
        public Action? Callback;
    }
    private readonly State? state;
    internal AudioHandle(State value) => state = value;
    public string Path => state?.Path ?? "";
    public bool IsPlaying => state?.Playing ?? false;
    public Vec3 Position { get => state?.Position ?? default; set { if (state != null) state.Position = value; } }
    public float Volume { get => state?.Volume ?? 0; set { if (state != null) state.Volume = value; } }
    public void Set(string parameter, float value) { }
    public void Stop() { if (state != null) state.Playing = false; }
    public void SetCallback(Action callback)
    {
        if (state != null) { state.Callback = callback; Audio.Track(state); }
    }
    public static implicit operator bool(AudioHandle handle) => handle.IsPlaying;
}
