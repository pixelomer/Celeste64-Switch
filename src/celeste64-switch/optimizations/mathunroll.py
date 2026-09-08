def optimize_mathunroll(out):
    path = out / 'foster/switch_render_math.c'
    text = path.read_text()
    original = '    for (int i = 0; i < 4; i++)'
    assert text.count(original) == 3
    path.write_text(text.replace(original, '    #pragma GCC unroll 4\n' + original))
