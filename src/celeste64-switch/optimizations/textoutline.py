def optimize_textoutline(out, port, override):
    (out / 'managed/Game/OutlinedText.cs').write_text((port / 'optimizations/OutlinedText.cs').read_text())
    override('Helpers/UI.cs', [('var font = Language.Current.SpriteFont;\n\t\tfor (int x = -1; x <= 1; x++)', 'var font = Language.Current.SpriteFont;\n        if (OutlinedText.TryDraw(batch, font, text, at, justify, color)) return;\n\t\tfor (int x = -1; x <= 1; x++)')])
