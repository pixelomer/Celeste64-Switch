"""Generate a latest-game / legacy-native-backend integration candidate.

The old preparation pipeline supplies the proven native/audio bootstrap. Game
sources below come from 6edfe1e; no gameplay source is replaced with v1.1.1.
"""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, sys
root = Path(__file__).resolve().parents[3]
here = Path(__file__).resolve().parent
name = 'celeste64-switch-v120-bootstrap'
out = root / 'artifacts' / name
latest = root / 'third_party/upstream/celeste64-v1.2-research'
modern = root / 'third_party/upstream/foster'
assert subprocess.check_output(['git', '-C', str(latest), 'rev-parse', 'HEAD'], text=True).strip() == '6edfe1ebd2a21a6134d7675a28e357891025407e'
assert subprocess.check_output(['git', '-C', str(modern), 'rev-parse', 'HEAD'], text=True).strip() == 'a5b574f36e5d8928a4d47566c7b924140b653c85'
env = {k: v for k, v in os.environ.items() if not k.startswith('CELESTE64_')}
env.update(CELESTE64_BUILD_NAME=name, CELESTE64_OPTIMIZATIONS='', CELESTE64_AUDIO_PREFERRED_CORE='2', CELESTE64_AOT_OPTIMIZE='aggressive-inlining')
env['CELESTE64_MESA_WORKER'] = os.environ.get('CELESTE64_V120_MESA_WORKER', '0')
env['CELESTE64_MESA_LARGE_UPLOADS'] = env['CELESTE64_MESA_WORKER']
subprocess.run(['python3', str(here.parent / 'prepare.py')], env=env, check=True)

def replace(text, old, new, count=1):
    assert text.count(old) == count, (old, text.count(old), count)
    return text.replace(old, new)
gd = out / 'managed/Game'
for file in gd.glob('*.cs'):
    file.unlink()
for file in (latest / 'Source').rglob('*.cs'):
    relative = file.relative_to(latest / 'Source')
    if relative.parts[0] == 'Audio' or relative.name == 'Program.cs':
        continue
    text = file.read_text(encoding='utf-8-sig')
    text = text.replace('TextureWrap.Clamp', 'TextureWrap.ClampToEdge')
    text = text.replace('Normalized:', 'normalized:')
    text = re.sub('\\.TexCoords\\[([0-3])\\]', '.TexCoords\\1', text)
    text = text.replace('Calc.BetweenInterval(', 'Foster.Framework.Time.BetweenInterval(')
    if relative.name == 'Hair.cs':
        text = text.replace('mesh.SetVertices(', 'mesh.SetVertices<Vertex>(')
        text = text.replace('mesh.SetIndices(', 'mesh.SetIndices<int>(')
    if relative.name == 'SpriteRenderer.cs':
        text = text.replace('spriteMesh.SetVertices(', 'spriteMesh.SetVertices<SpriteVertex>(')
        text = text.replace('spriteMesh.SetIndices(', 'spriteMesh.SetIndices<int>(')
    if relative.name == 'Game.cs':
        text = replace(text, 'public class Game : App', 'public class Game : Module')
        text = replace(text, 'public Game(AppConfig config) : base(config)', 'public Game()')
        text = text.replace('protected override void', 'public override void')
        text = replace(text, 'private readonly Stack<Scene> scenes', 'public readonly GraphicsDevice GraphicsDevice = new();\n    public readonly Window Window = new();\n    private readonly Foster.V120.LegacyInputProvider inputProvider = new();\n    public Input Input => inputProvider.Input;\n    public string UserPath => App.UserPath;\n    public void Exit() => App.Exit();\n    public Time Time { get; private set; }\n    private readonly Stack<Scene> scenes')
        text = replace(text, '\t\tAudio.Update();', '        Time = Foster.V120.LegacyClock.Current;\n        inputProvider.Update(Time);\n        Audio.Update();')
        text = replace(text, 'public override void Render()\n\t{', 'public override void Render()\n\t{\n        Foster.V120.LegacyClock.AdvanceRenderFrame();\n        Time = Foster.V120.LegacyClock.Current;')
        text = text.replace('FMOD.Studio.EVENT_CALLBACK audioEventCallback', 'Action audioEventCallback')
        text = replace(text, 'private FMOD.RESULT MusicTimelineCallback(FMOD.Studio.EVENT_CALLBACK_TYPE type, IntPtr _event, IntPtr parameters)', 'private void MusicTimelineCallback()')
        text = replace(text, '\n\t\treturn FMOD.RESULT.OK;', '')
    if relative.name == 'Save.cs':
        text = text.replace('App app', 'Game app')
        text = replace(text, 'File.Copy(tempPath, savePath, true);', 'using var source = File.OpenRead(tempPath);\n            using var destination = File.Create(savePath);\n            source.CopyTo(destination);\n            destination.Flush();')
    if relative.name == 'Assets.cs':
        text = replace(text, 'private static string? contentPath = null;', 'private static string? contentPath = "romfs:/Content";')
        start = text.index('\tprivate static Material? LoadShader(')
        end = text.index('\n}\n', start)
        text = text[:start] + '    private static Material? LoadShader(GraphicsDevice gfx, string name)\n    {\n        var path = Path.Join(ContentPath, "Shaders", "Switch", name);\n        return new Material(new Shader(new ShaderCreateInfo(\n            File.ReadAllText(path + ".vertex.glsl"),\n            File.ReadAllText(path + ".fragment.glsl"))) { Name = name });\n    }\n' + text[end:]
    (gd / relative.name).write_text(text)
aliases = ['Input', 'Time', 'Keys', 'Buttons', 'Axes', 'MouseButtons', 'VirtualStick', 'VirtualAction', 'VirtualDevice', 'ActionBindingSet', 'StickBindingSet', 'GamepadProviders']
(gd / 'V120Aliases.cs').write_text('\n'.join((f'global using {n} = Foster.V120.{n};' for n in aliases)) + '\n')
program = (here.parent / 'managed/Program.cs').read_text().replace('1.1.1 FMOD', '1.2.0 (6edfe1e) FMOD').replace('sdmc:/switch/celeste64/', 'sdmc:/switch/celeste64-v120/')
(gd / 'Program.cs').write_text(program)
shutil.copy2(here.parent / 'managed/Audio.cs', gd / 'Audio.cs')
shutil.copy2(latest / 'Source/Audio/Events.cs', gd / 'Events.cs')
project = (gd / 'Celeste64.Switch.csproj').read_text()
start = project.index('<ItemGroup>')
end = project.index('<ProjectReference', start)
project = project[:start] + '<ItemGroup>\n' + project[end:]
project = project.replace('<Version>1.1.1</Version>', '<Version>1.2.0</Version><LangVersion>14.0</LangVersion>')
project = project.replace('1.0.0-alpha0031', '1.0.5').replace('Version="1.1.5"', 'Version="1.2.8"')
(gd / 'Celeste64.Switch.csproj').write_text(project)
fd = out / 'managed/Foster'
shutil.copy2(modern / 'Framework/Utility/Converters.cs', fd / 'V120Converters.cs')
for source in (modern / 'Framework/Input').rglob('*.cs'):
    if source.name == 'Cursor.cs':
        continue
    text = source.read_text(encoding='utf-8-sig').replace('namespace Foster.Framework;', 'using Foster.Framework;\nnamespace Foster.V120;')
    text = text.replace('Calc.OnInterval(', 'Foster.Framework.Time.OnInterval(').replace('Calc.ClampedMap(', 'TimeMath.ClampedMap(')
    text = text.replace('JsonConverters.', 'Foster.Framework.JsonConverters.')
    text = text.replace('Foster.Framework.Axes.', 'Foster.V120.Axes.')
    text = text.replace('SDL3.SDL.SDL_AddGamepadMapping(mapping);', 'LegacyInputProvider.AddMapping(mapping);')
    (fd / ('V120' + source.name)).write_text(text)
text = (modern / 'Framework/Utility/Time.cs').read_text().replace('namespace Foster.Framework;', 'using Foster.Framework;\nnamespace Foster.V120;')
text = text.replace('Calc.', 'TimeMath.')
(fd / 'V120Time.cs').write_text(text)
for source in here.glob('*.cs'):
    shutil.copy2(source, fd / source.name)
project = (fd / 'Foster.Framework.csproj').read_text().replace('<Version>0.1.18</Version>', '<Version>0.1.18</Version><LangVersion>14.0</LangVersion>')

def foster_patch(filename, changes):
    global project
    source = root / 'third_party/upstream/foster-0.1.18/Framework' / filename
    text = source.read_text(encoding='utf-8-sig')
    for old, new in changes:
        text = replace(text, old, new)
    (fd / source.name).write_text(text)
    project = project.replace('Exclude="', 'Exclude="' + str(source) + ';')
foster_patch('Graphics/Material.cs', [('public class Material', 'public partial class Material'), ('public Material() { }', 'public Material() { }\n    public Material(Material source) { source.CopyTo(this); }'), ('floatBuffer.AsSpan().CopyTo(material.floatBuffer);', 'floatBuffer.AsSpan().CopyTo(material.floatBuffer);\n        CopyStagesTo(material);'), ('internal unsafe void Apply()\n\t{', 'internal unsafe void Apply()\n\t{\n        SyncStages();')])
foster_patch('Graphics/Texture.cs', [('public class Texture :', 'public partial class Texture :')])
foster_patch('Graphics/Target.cs', [('public class Target : IResource', 'public partial class Target : IResource, IDrawableTarget')])
foster_patch('Graphics/Batcher.cs', [('public class Batcher', 'public partial class Batcher'), ('mat.Set(batch.MaterialState.MatrixUniform, matrix);\n\t\tmat.Set(batch.MaterialState.TextureUniform, texture);\n\t\tmat.Set(batch.MaterialState.SamplerUniform, batch.Sampler);', 'if (mat.Shader?.Has("type_VertexUniforms") == true)\n        {\n            mat.Vertex.SetUniformBuffer(matrix);\n            mat.Fragment.Samplers[0] = new(texture, batch.Sampler);\n            mat.Fragment.FlipTargetSamplers = false; // Batcher already flips target UVs.\n        }\n        else\n        {\n            mat.Set(batch.MaterialState.MatrixUniform, matrix);\n            mat.Set(batch.MaterialState.TextureUniform, texture);\n            mat.Set(batch.MaterialState.SamplerUniform, batch.Sampler);\n        }')])
foster_patch('Graphics/SpriteFont.cs', [('public class SpriteFont', 'public partial class SpriteFont')])
foster_patch('Graphics/DrawCommand.cs', [('public struct DrawCommand()', 'public partial struct DrawCommand()'), ('public bool DepthMask = false;', 'public bool DepthMask = false;\n    public bool DepthTestEnabled = true;')])
foster_patch('Graphics/Enums/TextureFormat.cs', [('Color = R8G8B8A8', 'Color = R8G8B8A8,\n    Depth16 = 3'), ('TextureFormat.Depth24Stencil8 => 4,', 'TextureFormat.Depth24Stencil8 => 4,\n            TextureFormat.Depth16 => 2,')])
(fd / 'Foster.Framework.csproj').write_text(project)
app = fd / 'App.cs'
text = app.read_text().replace('sdmc:/switch/celeste64', 'sdmc:/switch/celeste64-v120')
text = replace(text, 'Time.Advance(delta);', 'Time.Advance(delta);\n            Foster.V120.LegacyClock.Advance(delta);')
text = replace(text, 'Time.Advance(accumulator - Time.FixedStepMaxElapsedTime);', 'Time.Advance(accumulator - Time.FixedStepMaxElapsedTime);\n                Foster.V120.LegacyClock.Advance(accumulator - Time.FixedStepMaxElapsedTime);')
app.write_text(text)
main = out / 'source/main.c'
main.write_text(main.read_text().replace('sdmc:/switch/celeste64', 'sdmc:/switch/celeste64-v120'))
shutil.copytree(latest / 'Content', out / 'romfs/Content', dirs_exist_ok=True)
(out / 'excluded-editor-content.json').unlink(missing_ok=True)
if os.environ.get('CELESTE64_V120_RUNTIME_CONTENT') == '1':
    from runtime_content import prune_editor_content
    prune_editor_content(out)
cross = root / 'artifacts/spirv-cross-build/spirv-cross'
shader_dest = out / 'romfs/Content/Shaders/Switch'
shader_dest.mkdir(exist_ok=True)
for name in ['Default', 'Edge', 'Sprite']:
    for stage in ['vertex', 'fragment']:
        args = [str(cross), str(latest / f'Content/Shaders/Compiled/{name}.{stage}.spv'), '--version', '330', '--no-es', '--flatten-ubo']
        if stage == 'vertex':
            args += ['--fixup-clipspace']
        text = subprocess.check_output(args, text=True)
        if name == 'Default' and stage == 'vertex':
            pattern = 'mat4\\(type_JointUniforms\\[int\\(in_var_TEXCOORD4\\.[xyzw]\\)[^;]*?\\+ 3\\]\\)'
            text, count = re.subn(pattern, lambda match: 'transpose(' + match[0] + ')', text)
            assert count == 4, ('row-major joint array reads', count)
        text = text.replace('out_var_TEXCOORD', 'varying_TEXCOORD') if stage == 'vertex' else text.replace('in_var_TEXCOORD', 'varying_TEXCOORD')
        if stage == 'fragment':
            helpers = []
            for sampler in re.findall('uniform sampler2D (\\w+);', text):
                slot = 1 if 'CombinedDepth' in sampler else 0
                function = f'c64_sample{slot}'
                text = text.replace(f'texture({sampler}, ', function + '(')
                helpers.append(f'uniform float c64_flip{slot};\nvec4 {function}(vec2 uv) {{ if(c64_flip{slot}>0.0) uv.y=1.0-uv.y; return texture({sampler},uv); }}\n')
            text = text.replace('void main()', ''.join(helpers) + '\nvoid main()')
        (shader_dest / f'{name}.{stage}.glsl').write_text(text)
header = root / 'third_party/upstream/foster-0.1.18/Platform/include/foster_platform.h'
(out / 'foster/foster_platform.h').write_text(replace(header.read_text(), 'FOSTER_TEXTURE_FORMAT_DEPTH24_STENCIL8,', 'FOSTER_TEXTURE_FORMAT_DEPTH24_STENCIL8,\n    FOSTER_TEXTURE_FORMAT_DEPTH16,'))
gl = out / 'foster/foster_renderer_opengl.c'
text = gl.read_text()
text = replace(text, '#define GL_DEPTH_STENCIL_ATTACHMENT 0x821A', '#define GL_DEPTH_STENCIL_ATTACHMENT 0x821A\n#define GL_DEPTH_ATTACHMENT 0x8D00\n#define GL_DEPTH_COMPONENT16 0x81A5\n#define GL_DEPTH_COMPONENT 0x1902')
text = replace(text, 'case FOSTER_TEXTURE_FORMAT_DEPTH24_STENCIL8:', 'case FOSTER_TEXTURE_FORMAT_DEPTH16:\n            result.glInternalFormat = GL_DEPTH_COMPONENT16;\n            result.glFormat = GL_DEPTH_COMPONENT;\n            result.glType = GL_UNSIGNED_SHORT;\n            break;\n        case FOSTER_TEXTURE_FORMAT_DEPTH24_STENCIL8:')
text = replace(text, 'if (attachments[i] == FOSTER_TEXTURE_FORMAT_DEPTH24_STENCIL8)', 'if (attachments[i] == FOSTER_TEXTURE_FORMAT_DEPTH16)\n        {\n            tex->glAttachment = GL_DEPTH_ATTACHMENT;\n        }\n        else if (attachments[i] == FOSTER_TEXTURE_FORMAT_DEPTH24_STENCIL8)')
gl.write_text(text)
make = out / 'Makefile'
app_title = 'Celeste 64 v1.2.0'
make_text = make.read_text().replace('APP_VERSION := 1.1.1-a1', 'APP_VERSION := 1.2.0-6edfe1e')
make_text, title_count = re.subn('^APP_TITLE := .*$', 'APP_TITLE := ' + app_title, make_text, flags=re.M)
assert title_count == 1
make.write_text(make_text)
(out / 'v120-inputs.json').write_text(json.dumps({'game': '6edfe1ebd2a21a6134d7675a28e357891025407e', 'foster_input': 'a5b574f36e5d8928a4d47566c7b924140b653c85', 'backend': '351d20640cb6d6323a1490fa5f5254b8269f783c', 'state': 'integration candidate; no performance claim'}, indent=2) + '\n')
print(out)
optimizations = [v for v in os.environ.get('CELESTE64_V120_OPTIMIZATIONS', '').split(',') if v]
render_math_options = {'renderprep', 'rendermath', 'nativemath', 'mathunroll', 'matrixpair'}
stage_options = {'stagebindings', 'nativeuniformcopy', 'drawableframe', 'nativehair', 'skinbindings', 'uniformrefs', 'stagefast'}
animation_options = {'animationmath', 'indexedcurves', 'morphneutral', 'nativeskin', 'affinemath', 'posematrix', 'srtmatrix'}
stage_options |= animation_options
stage_options.add('boxinflate')
stage_options.add('inflatedcull')
stage_options.add('stagecopybatch')
stage_options.add('scalarbounds')
stage_options.add('inversecache')
stage_options.add('renderinterfaces')
stage_options.add('leafinterop')
stage_options.add('spikemesh')
stage_options.add('streambuffers')
stage_options.add('posereuse')
allowed = {'spatial', 'late', 'frustum', 'collision', 'gridwalk', 'snow', 'snowphase', 'material', 'materialrefs', 'uniforms', 'glcache', 'textures', 'imagebytes', 'animation', 'sprites', 'spritefill', 'spritefields', 'snowsprite', 'snowfill', 'modelsort', 'shadowcache', 'hair', 'hairmesh', 'nativecull', 'modelbits', 'collisionmath', 'submitbatch'} | render_math_options | stage_options
assert not set(optimizations) - allowed, set(optimizations) - allowed
if optimizations:
    sys.path.insert(0, str(here.parent))
    from optimizations.prepare import optimize
    if 'animation' in optimizations:
        from animation_v120 import optimize_animation
        optimize_animation(out, here.parent, replace)
    optimize(out, here.parent, latest, root / 'third_party/upstream/foster-0.1.18', [v for v in optimizations if v != 'animation' and v not in render_math_options and (v not in stage_options)])

    def override(relative, changes):
        path = gd / Path(relative).name
        text = path.read_text()
        for change in changes:
            text = replace(text, *change)
        path.write_text(text)
    if set(optimizations) & render_math_options:
        from render_math_v120 import optimize_render
        optimize_render(out, here.parent, replace, override, optimizations)
    if 'uniformrefs' in optimizations:
        from uniform_refs import optimize_uniform_refs
        optimize_uniform_refs(out, replace, override)
    if 'inversecache' in optimizations:
        assert {'renderprep', 'nativemath'} <= set(optimizations)
        from inverse_cache import optimize_inverse_cache
        optimize_inverse_cache(out, replace, override)
    if 'renderinterfaces' in optimizations:
        from render_interfaces import optimize_render_interfaces
        optimize_render_interfaces(out, override)
    if 'skinbindings' in optimizations:
        assert 'animation' in optimizations
        from optimizations.skinbindings import optimize_skinbindings
        optimize_skinbindings(out, replace)
    for option in ['animationmath', 'indexedcurves', 'morphneutral', 'nativeskin', 'affinemath', 'posematrix', 'srtmatrix']:
        if option not in optimizations:
            continue
        dependencies = {'animationmath': {'animation', 'nativemath'}, 'indexedcurves': {'animation'}, 'morphneutral': {'animation'}, 'nativeskin': {'skinbindings', 'animationmath'}, 'affinemath': {'animationmath'}, 'posematrix': {'affinemath'}, 'srtmatrix': {'affinemath'}}
        assert dependencies[option] <= set(optimizations), (option, dependencies[option])
        import importlib
        apply = getattr(importlib.import_module('optimizations.' + option), 'optimize_' + option)
        if option in {'nativeskin', 'affinemath', 'posematrix'}:
            apply(out, replace)
        else:
            apply(out, here.parent, replace)
    if 'nativehair' in optimizations:
        assert {'hair', 'hairmesh', 'rendermath'} <= set(optimizations)
        from optimizations.nativehair import optimize_nativehair
        optimize_nativehair(out, here.parent, override)
    if 'drawableframe' in optimizations:
        from drawable_frame_v120 import optimize_drawableframe
        optimize_drawableframe(out, here.parent, override)
    if 'stagebindings' in optimizations:
        from stage_bindings import optimize_stage_bindings
        optimize_stage_bindings(out, here, replace, 'nativeuniformcopy' in optimizations)
    elif 'nativeuniformcopy' in optimizations:
        raise ValueError('nativeuniformcopy requires stagebindings in the current shader adapter')
    if 'stagefast' in optimizations:
        assert {'stagebindings', 'nativeuniformcopy'} <= set(optimizations)
        from stage_fast import optimize_stage_fast
        optimize_stage_fast(out, replace)
    if 'stagecopybatch' in optimizations:
        assert {'stagebindings', 'nativeuniformcopy', 'stagefast'} <= set(optimizations)
        from stage_copy_batch import optimize_stage_copy_batch
        optimize_stage_copy_batch(out, here, replace)
    if 'scalarbounds' in optimizations:
        assert 'boxinflate' not in optimizations
        from scalar_bounds import optimize_scalar_bounds
        optimize_scalar_bounds(out, replace, override)
    if 'boxinflate' in optimizations:
        from box_inflate import optimize_box_inflate
        optimize_box_inflate(out, here, replace, override)
    if 'inflatedcull' in optimizations:
        assert 'nativecull' in optimizations
        from box_inflate import optimize_inflated_cull
        optimize_inflated_cull(out, here, replace, override)
    if 'streambuffers' in optimizations:
        from stream_buffers import optimize_stream_buffers
        optimize_stream_buffers(out, replace)
    if 'posereuse' in optimizations:
        assert {'animation', 'drawableframe'} <= set(optimizations)
        from pose_reuse import optimize_pose_reuse
        optimize_pose_reuse(out, replace)
    if 'spikemesh' in optimizations:
        from spike_mesh_cache import optimize_spike_mesh
        optimize_spike_mesh(out, here, replace)
    if 'leafinterop' in optimizations:
        assert {'stagecopybatch', 'nativeuniformcopy', 'nativemath'} <= set(optimizations)
        from leaf_interop import optimize_leaf_interop
        optimize_leaf_interop(out, replace)
if os.environ.get('CELESTE64_V120_ASSET_QUEUE') == '1':
    from asset_queue import optimize_asset_queue
    optimize_asset_queue(out, replace)
if os.environ.get('CELESTE64_V120_ASSET_ORDER') == '1':
    from asset_order import optimize_asset_order
    optimize_asset_order(out, replace)
if os.environ.get('CELESTE64_V120_ASSET_WORKERS') == '1':
    from asset_workers import optimize_asset_workers
    optimize_asset_workers(out, replace)
options = json.loads((out / 'build-options.json').read_text())
options.update(game_commit='6edfe1ebd2a21a6134d7675a28e357891025407e', game_version='1.2.0', foster_input_commit='a5b574f36e5d8928a4d47566c7b924140b653c85', spirv_cross_commit='be71ee8c12cd7dc5ca8fa9581f708c2e8561fe2a', spirv_cross_binary_sha256=hashlib.sha256(cross.read_bytes()).hexdigest(), aot_dedup=os.environ.get('CELESTE64_V120_AOT_DEDUP') == '1', asset_queue=os.environ.get('CELESTE64_V120_ASSET_QUEUE') == '1', asset_order=os.environ.get('CELESTE64_V120_ASSET_ORDER') == '1', asset_workers=os.environ.get('CELESTE64_V120_ASSET_WORKERS') == '1', runtime_content=os.environ.get('CELESTE64_V120_RUNTIME_CONTENT') == '1', source_optimizations=optimizations, save_directory='sdmc:/switch/celeste64-v120', sharpgltf_version='1.0.5', sledge_version='1.2.8', animation_runtime_commit='4b28af2b6e5e30c6bade3f8baaf6b5e1a67ceb98' if 'animation' in optimizations else None, nacp_title=app_title, nacp_version='1.2.0-6edfe1e')
(out / 'build-options.json').write_text(json.dumps(options, indent=2) + '\n')
