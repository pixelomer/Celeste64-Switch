"""Start larger independent asset jobs first; retain the existing parsers."""

def optimize_asset_order(out, replace):
    p = out / 'managed/Game/Assets.cs'
    s = p.read_text()
    for folder, suffix in [('mapsPath', 'map'), ('modelPath', 'glb')]:
        expression = f'Directory.EnumerateFiles({folder}, "*.{suffix}", SearchOption.AllDirectories)'
        s = replace(s, expression, expression + '.OrderByDescending(file => new FileInfo(file).Length)')
    p.write_text(s)
