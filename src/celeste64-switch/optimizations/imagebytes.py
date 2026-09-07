def optimize_imagebytes(out, replace, override):
    path = out / 'managed/Foster/Image.cs'
    text = path.read_text()
    text = replace(text, '\t~Image()', '    /// <summary>Decode encoded image bytes synchronously without copying them.</summary>\n    public Image(ReadOnlySpan<byte> encodedData)\n    {\n        Load(encodedData);\n    }\n\n\t~Image()')
    text = replace(text, '\t\t// load image from byte data', '        Load(data.AsSpan());\n    }\n\n    private unsafe void Load(ReadOnlySpan<byte> data)\n    {\n\t\t// load image from byte data')
    path.write_text(text)
    override('Graphics/SkinnedTemplate.cs', [('using var stream = new MemoryStream(logicalImage.Content.Content.ToArray());\n\t\t\tvar img = new Image(stream);', 'var img = new Image(logicalImage.Content.Content.Span);')])
