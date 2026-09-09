using System.Numerics;
using System.Runtime.InteropServices;
using Legacy = Foster.Framework.Input;
namespace Foster.V120;

// Preserve Foster 0.4.2's action/filter/buffering implementation. Only the raw
// platform events are sourced from the already-working SDL2/libnx backend.
public sealed class LegacyInputProvider : InputProvider
{
    private readonly bool[] connected = new bool[32];
    private readonly ControllerID[] ids = new ControllerID[32];
    private uint generation;
    public override void SetClipboard(string text) => Legacy.SetClipboardString(text);
    public override string GetClipboard() => Legacy.GetClipboardString();
    public override void Rumble(ControllerID id, float low, float high, float duration)
    {
        // The game has no rumble calls. Make unsupported use explicit rather
        // than pretending it was delivered by the legacy wrapper.
        throw new NotSupportedException("Controller rumble is not exposed by the legacy Foster backend");
    }
    [DllImport("SDL2", EntryPoint="SDL_GameControllerAddMapping")]
    private static extern int AddMappingNative([MarshalAs(UnmanagedType.LPUTF8Str)] string mapping);
    public static void AddMapping(string mapping) => AddMappingNative(mapping);

    public override void Update(in Time time)
    {
        for (int i=0; i<Legacy.Controllers.Count; i++)
        {
            var current=Legacy.Controllers[i]; var previous=Legacy.LastState.Controllers[i];
            bool fresh=current.Connected && !connected[i];
            if (fresh)
            {
                ids[i]=new(++generation);
                ConnectController(ids[i],current.Name,current.Buttons,current.Axes,current.IsGamepad,
                    GamepadTypes.NintendoSwitchPro,current.Vendor,current.Product,current.Version);
            }
            else if (!current.Connected && connected[i]) DisconnectController(ids[i]);
            connected[i]=current.Connected;
            if (!current.Connected) continue;
            for (int b=0;b<current.Buttons;b++)
            {
                if(current.Pressed(b)) ControllerButton(ids[i],b,true,time.Elapsed);
                if(current.Released(b)) ControllerButton(ids[i],b,false,time.Elapsed);
                if(fresh && current.Down(b) && !current.Pressed(b)) ControllerButton(ids[i],b,true,time.Elapsed);
            }
            for(int a=0;a<current.Axes;a++)
                if(fresh || current.Axis(a)!=previous.Axis(a)) ControllerAxis(ids[i],a,current.Axis(a),time.Elapsed);
        }
        for(int i=0;i<Foster.Framework.Keyboard.MaxKeys;i++)
        {
            var key=(Foster.Framework.Keys)i;
            if(Legacy.Keyboard.Pressed(key)) Key(i,true,time.Elapsed);
            if(Legacy.Keyboard.Released(key)) Key(i,false,time.Elapsed);
        }
        foreach(var text in Legacy.Keyboard.Text.GetChunks()) Text(text.Span);
        var mouse=Legacy.Mouse;
        // Both backends expose SDL's mouse button IDs.
        foreach(var pair in new[] {(Foster.Framework.MouseButtons.Left,1),(Foster.Framework.MouseButtons.Middle,2),(Foster.Framework.MouseButtons.Right,3)})
        {
            if(mouse.Pressed(pair.Item1)) MouseButton(pair.Item2,true,time.Elapsed);
            if(mouse.Released(pair.Item1)) MouseButton(pair.Item2,false,time.Elapsed);
        }
        MouseMove(mouse.Position,mouse.Position-Legacy.LastState.Mouse.Position,time.Elapsed);
        MouseWheel(mouse.Wheel);
        base.Update(time);
    }
}

internal static class TimeMath
{
    public static float ClampedMap(float val,float min,float max,float newMin=0,float newMax=1)
        => Math.Clamp((val-min)/(max-min),0,1)*(newMax-newMin)+newMin;
    public static bool OnInterval(double time,double delta,double interval,double offset=0)
        => Math.Floor((time-offset-delta)/interval)<Math.Floor((time-offset)/interval);
    public static int IntervalCount(double time,double delta,double interval,double offset=0)
        => (int)(Math.Floor((time-offset)/interval)-Math.Floor((time-offset-delta)/interval));
    public static bool BetweenInterval(double time,double interval,double offset=0)
        => (time-offset)%(interval*2)>=interval;
    public static bool BetweenInterval(double time,double a,double b,double offset)
        => (time-offset)%(a+b)>=a;
    public static T CycleInterval<T>(double time,double interval,double offset,params ReadOnlySpan<T> options)
        => options[(int)((time-offset)/interval)%options.Length];
    public static T CycleInterval<T>(double time,double interval,params ReadOnlySpan<T> options)
        => options[(int)(time/interval)%options.Length];
    public static TimeSpan Modulo(this TimeSpan value,TimeSpan modulus)
        => TimeSpan.FromTicks((value.Ticks%modulus.Ticks+modulus.Ticks)%modulus.Ticks);
}
