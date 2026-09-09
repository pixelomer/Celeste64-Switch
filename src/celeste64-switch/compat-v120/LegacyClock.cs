namespace Foster.V120;

// Mirror current Foster's clock at the legacy loop's exact advance points,
// including discarded catch-up time. The next gameplay Delta remains one step
// after a long stall or HOME suspension, as it does in current Foster.
public static class LegacyClock
{
    public static Time Current { get; private set; }
    public static void Reset() => Current = default;
    public static void Advance(TimeSpan delta) => Current = Current.Advance(delta);
    public static void AdvanceRenderFrame() => Current = Current.AdvanceRenderFrame();
}
