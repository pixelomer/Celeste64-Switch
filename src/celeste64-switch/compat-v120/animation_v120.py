"""Build the pinned SharpGLTF runtime with materialized animation key arrays."""
import subprocess
COMMIT = '4b28af2b6e5e30c6bade3f8baaf6b5e1a67ceb98'

def optimize_animation(out, port, replace):
    upstream = port.parents[1] / 'third_party/upstream/sharpgltf-1.0.5'
    if not upstream.exists():
        raise RuntimeError('Run the v1.2.0 dependency bootstrap first')
    assert subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip() == COMMIT
    dest = out / 'managed/SharpGLTF'
    dest.mkdir(exist_ok=True)
    for generated in dest.glob('*.cs'):
        generated.unlink()
    for source in (upstream / 'src/SharpGLTF.Runtime/Runtime').glob('*.cs'):
        text = source.read_text(encoding='utf-8-sig')
        if source.name == 'NodeTemplate.cs':
            text = replace(text, 'curves.Scale?.CreateCurveSampler(isolateMemory)', 'CachedCurve.Create(curves.Scale)')
            text = replace(text, 'curves.Rotation?.CreateCurveSampler(isolateMemory)', 'CachedCurve.Create(curves.Rotation)')
            text = replace(text, 'curves.Translation?.CreateCurveSampler(isolateMemory)', 'CachedCurve.Create(curves.Translation)')
            text = replace(text, 'curves.GetMorphingSampler<Transforms.SparseWeight8>()?.CreateCurveSampler(isolateMemory)', 'CachedCurve.Create(curves.GetMorphingSampler<Transforms.SparseWeight8>())')
        (dest / source.name).write_text(text)
    for filename in ['Guard.cs', '_Extensions.cs']:
        (dest / filename).write_text((upstream / 'src/Shared' / filename).read_text(encoding='utf-8-sig'))
    helpers = ['using System.Linq;\nusing System.Numerics;\nusing SharpGLTF.Animations;\nusing SharpGLTF.Schema2;\nusing SharpGLTF.Transforms;\nnamespace SharpGLTF.Runtime;\ninternal static class CachedCurve {']
    for kind in ['Vector3', 'Quaternion', 'SparseWeight8']:
        helpers.append(f'internal static ICurveSampler<{kind}> Create(IAnimationSampler<{kind}> sampler)\n        {{\n            if (sampler == null) return null;\n            return sampler.InterpolationMode switch\n            {{\n                AnimationInterpolationMode.STEP => sampler.GetLinearKeys().ToArray().CreateSampler(isLinear: false, optimize: false),\n                AnimationInterpolationMode.LINEAR => sampler.GetLinearKeys().ToArray().CreateSampler(isLinear: true, optimize: false),\n                AnimationInterpolationMode.CUBICSPLINE => sampler.GetCubicKeys().ToArray().CreateSampler(optimize: false),\n                _ => throw new System.NotImplementedException()\n            }};\n        }}')
    (dest / 'CachedCurve.cs').write_text('\n'.join(helpers) + '\n}\n')
    (dest / 'SharpGLTF.Runtime.Switch.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk">\n<PropertyGroup><TargetFramework>net9.0</TargetFramework><AssemblyName>SharpGLTF.Runtime.Switch</AssemblyName>\n<AllowUnsafeBlocks>true</AllowUnsafeBlocks><Nullable>disable</Nullable></PropertyGroup>\n<ItemGroup><PackageReference Include="SharpGLTF.Core" Version="1.0.5" /></ItemGroup>\n</Project>')
    project = out / 'managed/Game/Celeste64.Switch.csproj'
    project.write_text(replace(project.read_text(), '<PackageReference Include="SharpGLTF.Runtime" Version="1.0.5"/>', '<ProjectReference Include="../SharpGLTF/SharpGLTF.Runtime.Switch.csproj"/>'))
    (dest / 'UPSTREAM.txt').write_text(f'https://github.com/vpenades/SharpGLTF\n{COMMIT}\nRuntime source adapted; Core remains NuGet 1.0.5.\n')
    license_file = next(upstream.glob('LICENSE*'))
    (dest / 'LICENSE.txt').write_text(license_file.read_text())
