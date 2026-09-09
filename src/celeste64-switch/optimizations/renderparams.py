"""Inline the existing seven render-parameter setters into one managed call."""
PARAMETERS = [('NearPlane', 'state.Camera.NearPlane'), ('FarPlane', 'state.Camera.FarPlane'), ('Silhouette', 'state.Silhouette'), ('Time', '(float)Foster.Framework.Time.Duration.TotalSeconds'), ('SunDirection', 'state.SunDirection'), ('VerticalFogColor', 'state.VerticalFogColor'), ('Cutout', 'state.CutoutMode')]

def optimize_renderparams(out, override):
    source = (out / 'managed/Game/Materials.cs').read_text()
    blocks = []
    for name, value in PARAMETERS:
        import re
        match = re.search('public \\w+ ' + name + '\\s*\\{', source)
        assert match, name
        start = source.index('set', match.end())
        start = source.index('{', start)
        depth = 1
        end = start + 1
        while depth:
            if source[end] == '{':
                depth += 1
            if source[end] == '}':
                depth -= 1
            end += 1
        blocks.append('{ var value = ' + value + ';\n' + source[start + 1:end - 1] + '\n}')
    override('Graphics/Materials.cs', [('public string Name = string.Empty;', 'public string Name = string.Empty;\n    public void ApplyRenderParameters(in RenderState state)\n    {\n' + '\n'.join(blocks) + '\n    }')])
    original = '\n'.join(('\t\tmat.' + name + ' = ' + value.replace('state.Camera', 'Camera').replace('state.', '').replace('Foster.Framework.Time', 'Time') + ';' for name, value in PARAMETERS))
    override('Graphics/RenderState.cs', [(original, '        mat.ApplyRenderParameters(this);', 2)])
