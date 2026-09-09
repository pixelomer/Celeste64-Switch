using System.Numerics;
using System.Runtime.InteropServices;
namespace Foster.Framework;

// Compatibility boundary for the subset of Foster 0.4.2 used by Celeste64.
// All resource ownership and native draw submission remain in the legacy backend.
public sealed class GraphicsDevice
{
    public bool VSync { get => App.VSync; set => App.VSync=value; }
    public void Draw(DrawCommand command)
    {
        if(!command.DepthTestEnabled) command.DepthCompare=DepthCompare.None;
        command.Submit();
    }
}
public interface IDrawableTarget
{
    int WidthInPixels { get; }
    int HeightInPixels { get; }
    void Clear(Color color,float depth=1,int stencil=0,ClearMask mask=ClearMask.All);
}
public sealed class Window : IDrawableTarget
{
    public bool Focused => App.Focused;
    public bool Fullscreen { get => App.Fullscreen; set => App.Fullscreen=value; }
    public int WidthInPixels => App.WidthInPixels;
    public int HeightInPixels => App.HeightInPixels;
    public Vector2 SizeInPixels => App.SizeInPixels;
    public void Clear(Color color,float depth=1,int stencil=0,ClearMask mask=ClearMask.All) => Graphics.Clear(color,depth,stencil,mask);
    [DllImport("SDL2",EntryPoint="SDL_SetRelativeMouseMode")]
    private static extern int RelativeMode(int value);
    private bool relative;
    public void SetMouseRelativeMode(bool value)
    {
        if(relative==value) return;
        if(RelativeMode(value?1:0)==0) relative=value;
    }
}
public class Mesh<T> : Mesh where T : unmanaged, IVertex
{
    public Mesh(GraphicsDevice device) : base() { }
    public void SetVertices(ReadOnlySpan<T> data) => base.SetVertices<T>(data);
    public void SetVertices(Span<T> data) => base.SetVertices<T>(data);
    public void SetIndices(ReadOnlySpan<int> data) => base.SetIndices<int>(data);
    public void SetIndices(Span<int> data) => base.SetIndices<int>(data);
}
public partial class Texture
{
    public GraphicsDevice GraphicsDevice { get; } = new();
    public Texture(GraphicsDevice device,Image image,string? name=null) : this(image) { if(name!=null) Name=name; }
}
public partial class Target
{
    public int WidthInPixels => Width;
    public int HeightInPixels => Height;
    public Target(GraphicsDevice device,int width,int height) : this(width,height) { }
    public Target(GraphicsDevice device,int width,int height,TextureFormat[] formats) : this(width,height,formats) { }
}
public partial class Batcher
{
    public Batcher(GraphicsDevice device) : this() { }
    public void Render(Window window) => Render();
    public void Render(IDrawableTarget target) => Render(target as Target);
}
public partial class SpriteFont
{
    public SpriteFont(GraphicsDevice device,Font font,float size,ReadOnlySpan<int> codepoints) : this(font,size,codepoints) { }
}
public partial struct DrawCommand
{
    public DrawCommand(IDrawableTarget target,Mesh mesh,Material material) : this(target as Target,mesh,material)
    {
        if(target is not Foster.Framework.Target && target is not Window) throw new ArgumentException("Unsupported draw target",nameof(target));
    }
    public bool DepthWriteEnabled { get => DepthMask; set => DepthMask=value; }
    public int IndexOffset { get => MeshIndexStart; set => MeshIndexStart=value; }
    public int IndexCount { get => MeshIndexCount; set => MeshIndexCount=value; }
}

public readonly record struct StageSampler(Texture? Texture,TextureSampler Sampler)
{
    public readonly bool Assigned=true;
}
public partial class Material
{
    private MaterialStage? vertexStage,fragmentStage;
    public MaterialStage Vertex => vertexStage ??= new(this,true);
    public MaterialStage Fragment => fragmentStage ??= new(this,false);
    public void CopyFrom(Material other) => other.CopyTo(this);
    private void CopyStagesTo(Material other)
    {
        if(vertexStage!=null) vertexStage.CopyTo(other.Vertex);
        if(fragmentStage!=null) fragmentStage.CopyTo(other.Fragment);
    }
    private void SyncStages()
    {
        vertexStage?.Upload(); fragmentStage?.Upload();
    }
    public sealed class MaterialStage(Material owner,bool vertex)
    {
        private readonly byte[][] buffers=new byte[4][];
        public bool FlipTargetSamplers = true;
        public readonly StageSampler[] Samplers=new StageSampler[4];
        public Shader? Shader => owner.Shader;
        public void SetUniformBuffer<T>(in T value,int slot=0) where T:unmanaged
        {
            var source=MemoryMarshal.AsBytes(MemoryMarshal.CreateReadOnlySpan(in value,1));
            int size=(source.Length+15)&~15;
            if(buffers[slot]==null || buffers[slot].Length!=size) buffers[slot]=new byte[size];
            source.CopyTo(buffers[slot]);
        }
        public T GetUniformBuffer<T>(int slot=0) where T:unmanaged
            => buffers[slot]==null ? default : MemoryMarshal.Read<T>(buffers[slot]);
        internal void CopyTo(MaterialStage other)
        {
            for(int i=0;i<4;i++) other.buffers[i]=buffers[i]?.ToArray()!;
            Samplers.CopyTo(other.Samplers,0);
            other.FlipTargetSamplers=FlipTargetSamplers;
        }
        internal void Upload()
        {
            // SPIRV-Cross flattens each upstream uniform block to a float4 array.
            for(int i=0;i<4;i++)
            {
                string name=vertex ? (i==0?"type_VertexUniforms":"type_JointUniforms") : "type_FragmentUniforms";
                if(buffers[i]!=null && owner.Shader?.Has(name)==true)
                    owner.Set(name,MemoryMarshal.Cast<byte,float>(buffers[i]));
            }
            if(!vertex)
                for(int i=0;i<Samplers.Length;i++)
                {
                    if(!Samplers[i].Assigned) continue;
                    string name=i==0 ? (owner.Shader?.Name=="Edge" ? "SPIRV_Cross_CombinedTextureTextureSampler" : "SPIRV_Cross_CombinedTextureSampler") : "SPIRV_Cross_CombinedDepthDepthSampler";
                    if(owner.Shader?.Has(name)==true)
                    {
                        owner.Set(name,Samplers[i].Texture);
                        owner.Set(name+"_sampler",Samplers[i].Sampler);
                        if(owner.Shader.Has("c64_flip"+i))
                            owner.Set("c64_flip"+i,FlipTargetSamplers && (Samplers[i].Texture?.IsTargetAttachment ?? false)?1f:0f);
                    }
                }
        }
    }
}
