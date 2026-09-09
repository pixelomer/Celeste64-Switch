using System.Buffers;
using Foster.Framework;
using System.Numerics;
namespace Celeste64;

internal static class OutlinedText
{
    private struct Glyph
    {
        public SpriteFont.Character Character;
        public float Kerning;
        public bool ApplyKerning;
    }
    // Only share glyph lookup within this one outline operation. Dynamic strings,
    // mutable fonts and changing HUD values are re-read on every call.
    public static bool TryDraw(Batcher batch,SpriteFont font,ReadOnlySpan<char> text,Vector2 position,Vector2 justify,Color color)
    {
        if(text.Length>256 || text.IndexOf('\n')>=0)return false;
        float width=justify.X!=0 ? font.WidthOfLine(text) : 0;
        float height=justify.Y!=0 ? font.HeightOf(text) : 0;
        var glyphs=ArrayPool<Glyph>.Shared.Rent(Math.Max(1,text.Length));
        try
        {
            int count=0,last=0;
            for(int i=0;i<text.Length;i++)
                if(font.TryGetCharacter(text,i,out var ch,out int step))
                {
                    glyphs[count++]=new Glyph { Character=ch, ApplyKerning=last!=0,
                        Kerning=last!=0 ? font.GetKerning(last,ch.Codepoint) : 0 };
                    last=ch.Codepoint;i+=step-1;
                }
            for(int x=-1;x<=1;x++)
                for(int y=-1;y<=3;y++)
                    Draw(batch,font,glyphs,count,position+new Vector2(x,y),justify,width,height,Color.Black);
            Draw(batch,font,glyphs,count,position,justify,width,height,color);
        }
        finally { ArrayPool<Glyph>.Shared.Return(glyphs,clearArray:true); }
        return true;
    }
    private static void Draw(Batcher batch,SpriteFont font,Glyph[] glyphs,int count,Vector2 position,Vector2 justify,float width,float height,Color color)
    {
        // Match Batcher.Text arithmetic/rounding independently for each pass;
        // translating already-rounded base geometry is not generally equivalent.
        var at=position+new Vector2(0,font.Ascent);
        if(justify.X!=0)at.X-=justify.X*width;
        if(justify.Y!=0)at.Y-=justify.Y*height;
        at.X=Calc.Round(at.X);at.Y=Calc.Round(at.Y);
        for(int i=0;i<count;i++)
        {
            ref readonly var glyph=ref glyphs[i];
            ref readonly var ch=ref glyph.Character;
            if(glyph.ApplyKerning)at.X+=glyph.Kerning;
            if(ch.Subtexture.Texture!=null)batch.Image(ch.Subtexture,at+ch.Offset,color);
            at.X+=ch.Advance;
        }
    }
}
