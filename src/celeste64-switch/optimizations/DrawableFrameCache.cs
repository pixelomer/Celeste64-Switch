using SharpGLTF.Runtime;

namespace Celeste64;

// Scope is one synchronous World.Render, after actor and animation updates.
// Standalone render callers use token zero and always perform the original access.
internal sealed class DrawableFrameCache
{
    private SceneInstance? owner;
    private DrawableInstance[] values = [];
    private ulong[] frames = [];

    internal DrawableInstance Get(SceneInstance scene, int index, ulong frame)
    {
        if (frame == 0) return scene[index];
        if (!ReferenceEquals(owner, scene))
        {
            values = new DrawableInstance[scene.Count];
            frames = new ulong[scene.Count];
            owner = scene;
        }
        if (frames[index] != frame)
        {
            var value = scene[index];
            values[index] = value;
            frames[index] = frame;
            
        }
        else
        {
            // VALIDATE_HIT
            
        }
        return values[index];
    }
}
