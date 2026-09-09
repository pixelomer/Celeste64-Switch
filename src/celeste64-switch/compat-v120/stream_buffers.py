"""Orphan a buffer only when a write replaces its complete existing store."""

def optimize_stream_buffers(out, replace):
    p = out / 'foster/foster_renderer_opengl.c'
    s = p.read_text()
    for kind in ['vertex', 'index']:
        s = replace(s, f'if (totalSize > it->{kind}BufferSize)', f'// Complete replacement can use fresh storage while earlier draws\n    // retain the previous store. Partial writes preserve untouched bytes.\n    if (totalSize > it->{kind}BufferSize ||\n        (dataDestOffset == 0 && dataSize > 0 && dataSize == it->{kind}BufferSize))')
    p.write_text(s)
