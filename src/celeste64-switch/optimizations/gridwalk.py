def optimize_gridwalk(out, replace):
    path = out / 'managed/Game/SolidGridPartition.cs'
    text = path.read_text()
    text = replace(text, 'foreach (var it in Cell(x, y))', 'foreach (var it in System.Runtime.InteropServices.CollectionsMarshal.AsSpan(Cell(x, y)))')
    text = replace(text, 'queryStamp = 1;\n        }\n', 'queryStamp = 1;\n        }\n        var owner = queryOwner;\n        var stamp = queryStamp;\n')
    text = replace(text, 'it.GridQueryOwner != queryOwner || it.GridQueryStamp != queryStamp', 'it.GridQueryOwner != owner || it.GridQueryStamp != stamp')
    text = replace(text, 'it.GridQueryOwner = queryOwner;', 'it.GridQueryOwner = owner;')
    text = replace(text, 'it.GridQueryStamp = queryStamp;', 'it.GridQueryStamp = stamp;')
    path.write_text(text)
