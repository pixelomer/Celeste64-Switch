"""Create build inputs from pinned upstream sources without modifying checkouts."""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess
root = Path(__file__).resolve().parents[2]
port = root / 'src/celeste64-switch'
build_name = os.environ.get('CELESTE64_BUILD_NAME') or 'celeste64-switch'
out = root / 'artifacts' / build_name
game = root / 'third_party/upstream/celeste64-v1.1.1'
foster = root / 'third_party/upstream/foster-0.1.18'
mono = root / 'third_party/upstream/mono-nx'
for path, sha in [(game, 'bfc7a3ba6f35d25bd11b4c4bad749398f70034e2'), (foster, '351d20640cb6d6323a1490fa5f5254b8269f783c'), (mono, 'fec057748af9121d5cf363e772e817908d57c191')]:
    assert subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip() == sha
for d in ['managed/Game', 'managed/Foster', 'source', 'romfs', 'logs']:
    (out / d).mkdir(parents=True, exist_ok=True)
for d in ['managed/Game', 'managed/Foster']:
    for generated in (out / d).glob('*.cs'):
        generated.unlink()

def patch(source, dest, replacements):
    text = source.read_text(encoding='utf-8-sig')
    for old, new in replacements:
        assert text.count(old) == 1, (source, old, text.count(old))
        text = text.replace(old, new)
    if not dest.exists() or dest.read_text() != text:
        dest.write_text(text)
patch(game / 'Source/Game.cs', out / 'managed/Game/Game.cs', [('FMOD.Studio.EVENT_CALLBACK audioEventCallback', 'Action audioEventCallback'), ('private FMOD.RESULT MusicTimelineCallback(FMOD.Studio.EVENT_CALLBACK_TYPE type, IntPtr _event, IntPtr parameters)', 'private void MusicTimelineCallback()'), ('\n\t\treturn FMOD.RESULT.OK;', ''), ('public override void Update()\n\t{', 'public override void Update()\n\t{\n\t\tAudio.Update();')])
patch(game / 'Source/Data/Assets.cs', out / 'managed/Game/Assets.cs', [('private static string? contentPath = null;', 'private static string? contentPath = "romfs:/Content";')])
patch(foster / 'Framework/App.cs', out / 'managed/Foster/App.cs', [('UserPath = Platform.ParseUTF8(Platform.FosterGetUserPath());', 'UserPath = "sdmc:/switch/celeste64";'), ('Log.Info($"Platform: {RuntimeInformation.OSDescription} ({RuntimeInformation.OSArchitecture})");', 'Log.Info("Platform: Nintendo Switch (ARM64/libnx)");')])
(out / 'managed/Foster/MonoPInvokeCallbackAttribute.cs').write_text('namespace AOT;\n[System.AttributeUsage(System.AttributeTargets.Method)]\ninternal sealed class MonoPInvokeCallbackAttribute : System.Attribute\n{\n    public MonoPInvokeCallbackAttribute(System.Type delegateType) { }\n}\n')
patch(foster / 'Framework/Utility/Log.cs', out / 'managed/Foster/Log.cs', [(f'public static unsafe void {name}(IntPtr utf8)', f'[AOT.MonoPInvokeCallback(typeof(Platform.FosterLogFn))]\n\tpublic static unsafe void {name}(IntPtr utf8)') for name in ['Info', 'Warning', 'Error']])
input_text = (foster / 'Framework/Input/Input.cs').read_text(encoding='utf-8-sig')
import re
input_text, callback_count = re.subn('(\\tinternal static (?:unsafe )?void (On\\w+)\\()', lambda m: '\t[AOT.MonoPInvokeCallback(typeof(Platform.Foster' + m[2] + 'Fn))]\n' + m[1], input_text)
assert callback_count == 9
(out / 'managed/Foster/Input.cs').write_text(input_text)
app_file = out / 'managed/Foster/App.cs'
app = app_file.read_text()
exit_lambda = 'onExitRequest = () =>\n            {\n                if (OnExitRequested != null)\n                    OnExitRequested();\n                else\n                    Exit();\n            }'.replace('    ', '\t')
assert exit_lambda in app
app = app.replace(exit_lambda, 'onExitRequest = SwitchExitRequest')
app = app.replace('\n}', '\n    [AOT.MonoPInvokeCallback(typeof(Platform.FosterExitRequestFn))]\n    private static void SwitchExitRequest()\n    {\n        if (OnExitRequested != null) OnExitRequested(); else Exit();\n    }\n}\n')
app_file.write_text(app)
patch(foster / 'Framework/Images/Image.cs', out / 'managed/Foster/Image.cs', [('static unsafe void Write(IntPtr context, IntPtr data, int size)', '[AOT.MonoPInvokeCallback(typeof(Platform.FosterWriteFn))]\n\t\tstatic unsafe void Write(IntPtr context, IntPtr data, int size)')])
patch(foster / 'Framework/Input/Controller.cs', out / 'managed/Foster/Controller.cs', [('return Gamepads.Xbox;', 'return Gamepads.Nintendo; // Horizon exposes Nintendo button positions.')])
patch(game / 'Source/Data/Save.cs', out / 'managed/Game/Save.cs', [('File.Copy(tempPath, savePath, true);', 'using var source = File.OpenRead(tempPath);\n            using var destination = File.Create(savePath);\n            source.CopyTo(destination);\n            destination.Flush();\n            Console.WriteLine("CELESTE64_SWITCH SAVED " + savePath);')])
(out / 'managed/Game/Celeste64.Switch.csproj').write_text(f'''<Project Sdk="Microsoft.NET.Sdk">\n<PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><AllowUnsafeBlocks>true</AllowUnsafeBlocks><DefineConstants>{''}</DefineConstants><Version>1.1.1</Version><CopyLocalLockFileAssemblies>true</CopyLocalLockFileAssemblies></PropertyGroup>\n<ItemGroup><Compile Include="{game}/Source/**/*.cs" Exclude="{game}/Source/Audio/**/*.cs;{game}/Source/Game.cs;{game}/Source/Data/Assets.cs;{game}/Source/Data/Save.cs;{game}/Source/Program.cs"/><Compile Include="{port}/managed/*.cs"/><Compile Include="{game}/Source/Audio/Events.cs"/>\n<ProjectReference Include="../Foster/Foster.Framework.csproj"/>\n<PackageReference Include="SharpGLTF.Runtime" Version="1.0.0-alpha0031"/><PackageReference Include="Sledge.Formats.Map" Version="1.1.5"/></ItemGroup></Project>''')
(out / 'managed/Foster/Foster.Framework.csproj').write_text(f'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net9.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><AllowUnsafeBlocks>true</AllowUnsafeBlocks><Version>0.1.18</Version></PropertyGroup><ItemGroup><Compile Include="{foster}/Framework/**/*.cs" Exclude="{foster}/Framework/App.cs;{foster}/Framework/Utility/Log.cs;{foster}/Framework/Input/Input.cs;{foster}/Framework/Input/Controller.cs;{foster}/Framework/Images/Image.cs;{foster}/Framework/obj/**/*.cs;{foster}/Framework/bin/**/*.cs"/></ItemGroup></Project>')
patch(mono / 'native/aot/source/main.c', out / 'source/main.c', [('#include <unistd.h>', '#include <unistd.h>\n#include <sys/stat.h>'), ('    romfsInit();', '    mkdir("sdmc:/switch", 0777);\n    mkdir("sdmc:/switch/celeste64", 0777);\n    romfsInit();')])
make = (mono / 'native/aot/Makefile').read_text().replace('aot_example', 'celeste64-switch')
make = 'APP_TITLE := Celeste 64 (silent Switch)\nAPP_AUTHOR := Celeste Team / homebrew port\nAPP_VERSION := 1.1.1-a1\n' + make
icon_input = root / 'artifacts/celeste64-switch-metadata/icon.jpg'
icon = out / 'icon.jpg'
if icon_input.exists():
    shutil.copyfile(icon_input, icon)
    make = 'ICON := icon.jpg\n' + make
else:
    icon.unlink(missing_ok=True)
make += '\n$(OUTPUT).nro: $(APP_ICON)\n'
make = make.replace('../shared', str(mono / 'native/shared'))
make = make.replace('$(OUTPUT).elf\t:\t$(OFILES)', '$(OUTPUT).elf\t:\t$(OFILES) $(AOT_FILES)')
make = make.replace('$(CURDIR)/$(dir)', '$(abspath $(dir))')
make = make.replace('source \\', 'source \\\n                foster \\')
make = make.replace('-DDLSHIM_DISABLE=1', f'-DDLSHIM_DISABLE=1 -DFOSTER_OPENGL_ENABLED -I{foster}/Platform/include -I{foster}/Platform/src -I$(PORTLIBS)/include/SDL2')
make = make.replace('-pthread -lnx -lm -lstdc++', '-Wl,--start-group -lSDL2 -lEGL -lglapi -ldrm_nouveau -pthread -lnx -lm -lstdc++ -Wl,--end-group')
(out / 'Makefile').write_text(make)
(out / 'foster').mkdir(exist_ok=True)
for generated in (out / 'foster').glob('switch_*.c'):
    generated.unlink()
for file in (foster / 'Platform/src').glob('*.c'):
    text = file.read_text().replace('SDL_GL_MULTISAMPLEBUFFERS, 1', 'SDL_GL_MULTISAMPLEBUFFERS, 0').replace('SDL_GL_MULTISAMPLESAMPLES, 4', 'SDL_GL_MULTISAMPLESAMPLES, 0')
    if file.name == 'foster_platform.c':
        text = '#include <switch.h>\n' + text
        old = 'SDL_GetWindowSizeInPixels(fstate.window, width, height);'
        assert text.count(old) == 1
        text = text.replace(old, 'SDL_GetWindowSizeInPixels(fstate.window, width, height);\n    int sdlWidth = *width, sdlHeight = *height;\n    u32 nativeWidth, nativeHeight;\n    if (R_SUCCEEDED(nwindowGetDimensions(nwindowGetDefault(), &nativeWidth, &nativeHeight)) &&\n        nativeWidth > 0 && nativeHeight > 0) {\n        *width = (int)nativeWidth;\n        *height = (int)nativeHeight;\n    }\n    static int lastSdlWidth = 0, lastNativeWidth = 0;\n    if (lastSdlWidth != sdlWidth || lastNativeWidth != *width) {\n        FosterLogInfo("Switch drawable: SDL=%dx%d native=%dx%d", sdlWidth, sdlHeight, *width, *height);\n        lastSdlWidth = sdlWidth;\n        lastNativeWidth = *width;\n    }')
        old = 'fstate.desc.onControllerAxis(index, axis, value);'
        assert text.count(old) == 1
        text = text.replace(old, 'fstate.desc.onControllerAxis(index, axis, value);')
    dest = out / 'foster' / file.name
    if not dest.exists() or dest.read_text() != text:
        dest.write_text(text)
(out / 'romfs/aot_config.ini').write_text('[mono]\nicu=romfs:/icudt77l.dat\nassembly_dir=/\nconfig_dir=/\ndefault_assembly=/Celeste64.Switch.dll\n[nx]\nsvc_io_redirect=true\nexit_process_on_end=true\n')
shutil.copytree(game / 'Content', out / 'romfs/Content', ignore=shutil.ignore_patterns('Audio'), dirs_exist_ok=True)
optimizations = [name for name in os.environ.get('CELESTE64_OPTIMIZATIONS', '').split(',') if name]
if optimizations:
    from optimizations.prepare import optimize
    optimize(out, port, game, foster, optimizations)
from audio.prepare import prepare_audio
fm_flags = prepare_audio(root, out)
makefile = out / 'Makefile'
makefile.write_text(makefile.read_text().replace('-DDLSHIM_DISABLE=1', '-DDLSHIM_DISABLE=1' + fm_flags).replace('Celeste 64 (silent Switch)', 'Celeste 64'))
source_files = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(port.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
(out / 'source-files.json').write_text(json.dumps(source_files, indent=2) + '\n')
(out / 'build-options.json').write_text(json.dumps({'port_source_commit': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(), 'port_source_files_sha256': hashlib.sha256((out / 'source-files.json').read_bytes()).hexdigest(), 'nro_icon_sha256': hashlib.sha256(icon.read_bytes()).hexdigest() if icon.exists() else None, 'animation_runtime_commit': '5a33d5452528d827ac55727f302d8a91a75c4186' if 'animation' in optimizations else None, 'build_name': build_name, 'mesa_large_uploads': os.environ.get('CELESTE64_MESA_LARGE_UPLOADS') == '1', 'audio_backend': 'FMOD Android ARM64 2.02.18 via libnx', 'audio_inputs_sha256': hashlib.sha256((out / 'audio-inputs.json').read_bytes()).hexdigest(), 'aot_optimize': os.environ.get('CELESTE64_AOT_OPTIMIZE') or 'compiler defaults', 'managed_configuration': 'Release', 'native_optimization': '-O2', 'mono_sdk_configuration': 'Debug', 'runtime_mode': 'MONO_AOT_MODE_FULL', 'aot_trampolines': {'specific': 65536, 'static_rgctx': 32768, 'imt': 4096, 'gsharedvt_arg': 8192}, 'source_optimizations': optimizations}, indent=2) + '\n')
print(out)
