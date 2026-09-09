def optimize_textoutline(out, port, override):
    import os
    source = (port / 'optimizations/OutlinedText.cs').read_text()
    (out / 'managed/Game/OutlinedText.cs').write_text(source)
    override('Helpers/UI.cs', [('var font = Language.Current.SpriteFont;\n\t\tfor (int x = -1; x <= 1; x++)', 'var font = Language.Current.SpriteFont;\n        if (OutlinedText.TryDraw(batch, font, text, at, justify, color)) return;\n\t\tfor (int x = -1; x <= 1; x++)')])
