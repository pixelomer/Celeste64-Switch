"""Generate the current game with the selected optimizations and full FMOD API.

Linux ARM64 is an intermediate ILC code-generation target. Its runtime archives
are not a substitute for the source-built Horizon runtime.
"""
from pathlib import Path
import json, os, re, shutil, subprocess, sys
import xml.etree.ElementTree as ET

here = Path(__file__).resolve().parent
root = here.parents[2]
subprocess.run([sys.executable, str(here.parent / "compat-v120/prepare.py")], check=True)
source = root / "artifacts/celeste64-switch-v120-bootstrap"
out = root / "artifacts/celeste64-nativeaot-managed"
out.mkdir(parents=True, exist_ok=True)
# Remove only this generated managed tree, including stale compiler objects.
if (out / "managed").exists():
    shutil.rmtree(out / "managed")
shutil.copytree(source / "managed", out / "managed", ignore=shutil.ignore_patterns("bin", "obj"))
project = out / "managed/Game/Celeste64.Switch.csproj"
tree = ET.parse(project)
props = tree.getroot().find("PropertyGroup")
props.find("OutputType").text = "Library"
ET.SubElement(props, "PublishAot").text = "true"
ET.SubElement(props, "NativeLib").text = "Static"
# Full culture/JSON behavior is retained; NativeAOT warnings are not suppressed.
items = ET.SubElement(tree.getroot(), "ItemGroup")
# Linux's inline TLS sequence reads TPIDR_EL0. Horizon uses libnx software TLS;
# retain the runtime helper path instead of relying on a fabricated Linux TCB.
ET.SubElement(items, "IlcArg", Include="--noinlinetls")
for name in ("__Internal", "FosterPlatform"):
    ET.SubElement(items, "DirectPInvoke", Include=name)
tree.write(project, encoding="unicode")
shutil.copy2(here / "EntryPoint.cs", project.parent / "NativeAotEntryPoint.cs")
for name in ("build-options.json", "source-files.json", "v120-inputs.json", "audio-inputs.json"):
    if (source / name).exists():
        shutil.copy2(source / name, out / name)
# Compatibility preparation originated in the Mono pipeline. Its compiler
# settings do not describe the NativeAOT object that this stage actually emits.
options_path = out / "build-options.json"
options = json.loads(options_path.read_text())
for key in ("aot_optimize", "mono_sdk_configuration", "aot_trampolines",
            "aot_dedup", "aot_dedup_keep"):
    options.pop(key, None)
options.update(runtime_mode="NativeAOT", ilc_version="9.0.3",
               ilc_optimization="Speed", inline_thread_statics=False)
# NativeAOT generates SIMD matrix code directly; the Mono preset retains its
# native helpers. Describe only the source switches present in this build.
import importlib.util
spec = importlib.util.spec_from_file_location("framework_math", here / "framework-math.py")
math_adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(math_adapter)
assert math_adapter.REMOVED <= set(options["source_optimizations"])
math_adapter.apply(out / "managed")
options["source_optimizations"] = [x for x in options["source_optimizations"] if x not in math_adapter.REMOVED]
options["framework_matrix_math"] = True
options_path.write_text(json.dumps(options, indent=2) + "\n")
(out / "stage.json").write_text(json.dumps({
    "stage": "managed-nativeaot-compilation-only",
    "runtime_package": "9.0.3",
    "ilc_target": "linux-arm64",
    "inline_thread_statics": False,
    "horizon_runtime_validated": False,
    "fmod": "2.02.18",
    "entrypoint": "C64ManagedMain",
    "framework_matrix_math": True,
}, indent=2) + "\n")
print(out, flush=True)

# Build the pinned SharpGLTF Core source so its broad JsonNode reflection roots
# can be removed. Parse/DeepClone use the built-in .NET 9 DOM implementation;
# rooting every method also pulls unsupported generic serialization into ILC.
core_source = root / "third_party/upstream/sharpgltf-1.0.5/src"
core = out / "managed/SharpGLTF.Core"
shutil.copytree(core_source / "SharpGLTF.Core", core,
                ignore=shutil.ignore_patterns("bin", "obj", "*.csproj"))
for name in ("Guard.cs", "_Extensions.cs"):
    shutil.copy2(core_source / "Shared" / name, core / name)
for name in ("Schema2/gltf.ExtraProperties.cs", "IO/UnknownNode.cs"):
    path = core / name
    text = path.read_text(encoding="utf-8-sig")
    text, count = re.subn(r"^\s*\[DynamicDependency\(DynamicallyAccessedMemberTypes.All, typeof\(System.Text.Json.Nodes.Json(?:Array|Value|Object)\)\)\]\s*$", "", text, flags=re.M)
    assert count == 6, (name, count)
    path.write_text(text)
path = core / "Validation/ModelException.cs"
text = path.read_text(encoding="utf-8-sig")
start = text.index('            var logicalIndexProp =')
end = text.index('            if (logicalIndex >= 0)', start)
text = text[:start] + """            var logicalIndex = target switch
            {
                SharpGLTF.Schema2.LogicalChildOfRoot child => child.LogicalIndex,
                SharpGLTF.Schema2.MeshPrimitive primitive => primitive.LogicalIndex,
                SharpGLTF.Schema2.AnimationSampler sampler => sampler.LogicalIndex,
                SharpGLTF.Schema2.AnimationChannel channel => channel.LogicalIndex,
                _ => -1
            };

""" + text[end:]
path.write_text(text)
path = core / "Validation/ValidationContext.cs"
text = path.read_text(encoding="utf-8-sig")
start = text.index('            var pinfo =')
end = text.index('            return name + this.ToString();', start)
text = text[:start] + """            int? index = target switch
            {
                SharpGLTF.Schema2.LogicalChildOfRoot child => child.LogicalIndex,
                SharpGLTF.Schema2.MeshPrimitive primitive => primitive.LogicalIndex,
                SharpGLTF.Schema2.AnimationSampler sampler => sampler.LogicalIndex,
                SharpGLTF.Schema2.AnimationChannel channel => channel.LogicalIndex,
                _ => null
            };
            if (index.HasValue) name += $"[{index.Value}]";

""" + text[end:]
path.write_text(text)
(core / "SharpGLTF.Core.csproj").write_text("""<Project Sdk="Microsoft.NET.Sdk">
<PropertyGroup><TargetFramework>net9.0</TargetFramework><AssemblyName>SharpGLTF.Core</AssemblyName>
<Version>1.0.5</Version><AllowUnsafeBlocks>true</AllowUnsafeBlocks><Nullable>disable</Nullable>
<IsAotCompatible>true</IsAotCompatible></PropertyGroup></Project>
""")
runtime = out / "managed/SharpGLTF/SharpGLTF.Runtime.Switch.csproj"
text = runtime.read_text()
old = '<PackageReference Include="SharpGLTF.Core" Version="1.0.5" />'
assert text.count(old) == 1
runtime.write_text(text.replace(old, '<ProjectReference Include="../SharpGLTF.Core/SharpGLTF.Core.csproj" />'))
