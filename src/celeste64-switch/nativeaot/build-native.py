#!/usr/bin/env python3
"""Link the generated current-game object with the source-built Horizon runtime."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess
here=Path(__file__).resolve().parent
root=here.parents[2]
runtime=Path(os.environ['NATIVEAOT_RUNTIME_ROOT']).resolve()
if (runtime/'sdk-manifest.json').is_file():
    validator=runtime/'src/coreclr/nativeaot/Runtime/libnx/validate-sdk.py'
    runtime_revision=subprocess.check_output(['python3',str(validator),str(runtime)],text=True).strip()
else:
    runtime_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=runtime,text=True).strip()

icu=Path(os.environ.get('ICU_NX_INSTALL_DIR',str(root/'third_party/upstream/mono-nx/icu/libnx'))).resolve()
dkp=Path(os.environ['DEVKITPRO'])
source=root/'artifacts/celeste64-switch-v120-bootstrap'
managed=root/'artifacts/celeste64-nativeaot-managed'
out=root/'artifacts/celeste64-switch-nativeaot'
obj=managed/'managed/Game/obj/Release/net9.0/linux-arm64/native/Celeste64.Switch.o'
sdk=runtime/'artifacts/bin/coreclr/libnx.arm64.Release/aotsdk'
libs=runtime/'artifacts/bin/native/net9.0-libnx-Release-arm64'
for p in (obj,source/'Makefile',sdk/'libRuntime.WorkstationGC.a',libs/'libSystem.Native.a'):
    if not p.is_file():raise SystemExit('Missing build input: '+str(p))
response=obj.with_suffix('.ilc.rsp').read_text()
if '-r:'+str(sdk/'System.Private.CoreLib.dll') not in response.splitlines():
    raise SystemExit('Rebuild managed code with NATIVEAOT_RUNTIME_ROOT: Horizon path-aware CoreLib is required')
subprocess.run(['python3',str(here/'check-output.py')],check=True)
out.mkdir(parents=True,exist_ok=True)
# Copy generated port sources and assets; no Mono bootstrap or managed DLLs.
for name in ('foster','romfs'):
    target=out/name
    if target.exists():shutil.rmtree(target)
    shutil.copytree(source/name,target)
for path in (out/'romfs').glob('*.dll'):path.unlink()
managed_options = json.loads((managed/'build-options.json').read_text())
if managed_options.get('framework_matrix_math'):
    for name in ('switch_render_math.c', 'switch_matrix_pair.c', 'switch_srt_matrix.c'):
        (out/'foster'/name).unlink()

(out/'romfs/aot_config.ini').unlink(missing_ok=True)
shutil.copy2(icu/'share/icu/77.1/icudt77l.dat',out/'romfs/icudt77l.dat')
(out/'source').mkdir(exist_ok=True)
shutil.copy2(here/'main.c',out/'source/main.c')
for name in ('icon.jpg','build-options.json','v120-inputs.json','audio-inputs.json'):
    origin = managed if name == 'build-options.json' else source
    if (origin/name).exists():shutil.copy2(origin/name,out/name)
script=runtime/'src/coreclr/nativeaot/Runtime/libnx/create-linker-script.py'
subprocess.run(['python3',str(script),str(out/'switch.ld')],check=True)
specs=(dkp/'libnx/switch.specs').read_text()
anchor='-T %:getenv(DEVKITPRO /libnx/switch.ld)'
assert specs.count(anchor)==1
(out/'switch.specs').write_text(specs.replace(anchor,'-T '+str(out/'switch.ld')))
make=(source/'Makefile').read_text().replace(str(source),str(out))
start=make.index('ifeq ($(strip $(MONO_NX_ROOT)),)');end=make.index('endif',start)+len('endif')
make=make[:start]+make[end:]
make=re.sub(r'SOURCES\s*:=.*?\n\nDATA', 'SOURCES := source foster\n\nDATA',make,flags=re.S)
make=re.sub(r'INCLUDES\s*:=.*?\n\nROMFS', 'INCLUDES := include\n\nROMFS',make,flags=re.S)
make=re.sub(r'^\s*-I\$\(MONO_NX_ROOT\).*?\\\n','',make,flags=re.M)
make=make.replace('-specs=$(DEVKITPRO)/libnx/switch.specs','-specs=$(TOPDIR)/switch.specs -Wl,--eh-frame-hdr')
make=re.sub(r'^AOT_FILES :=.*$', 'AOT_FILES := '+str(obj),make,flags=re.M)
start=make.index('LIBS\t');end=make.index('\n#---',start)
# Preserve the existing SDL/Mesa/native renderer selection and linker wraps.
old=make[start:end]
renderer=old[old.index('-Wl,--start-group -lSDL2'):].strip()
native=[sdk/'libbootstrapperdll.o',sdk/'libRuntime.WorkstationGC.a',sdk/'libeventpipe-disabled.a',sdk/'libstandalonegc-disabled.a',libs/'libSystem.Native.a',libs/'libSystem.Globalization.Native.a',libs/'libSystem.IO.Compression.Native.a',icu/'lib/libicui18n.a',icu/'lib/libicuuc.a',icu/'lib/libicudata.a']
make=make[:start]+'LIBS := $(AOT_FILES) -Wl,--start-group '+' '.join(map(str,native))+' -lz '+renderer+' -Wl,--end-group\n'+make[end:]
# The inherited rules omit static archives and build flags from dependencies.
# Regenerating this Makefile must rebuild native units and relink the runtime.
make=make.replace('$(OUTPUT).elf\t:\t$(OFILES) $(AOT_FILES)',
                  '$(OUTPUT).elf\t:\t$(OFILES) $(AOT_FILES) $(TOPDIR)/Makefile '+' '.join(map(str,native)))
make=make.replace('$(OFILES_SRC)\t: $(HFILES_BIN)',
                  '$(OFILES_SRC)\t: $(HFILES_BIN) $(TOPDIR)/Makefile')
(out/'Makefile').write_text(make)
(out/'logs').mkdir(exist_ok=True)
env=os.environ|{'ICU_NX_INSTALL_DIR':str(icu)}
with (out/'logs/native-build.log').open('w') as log:
    subprocess.run(['make','-j4'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
manifest={'port_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
 'runtime_commit':runtime_revision,
 'inputs_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [obj,*native,*sorted(sdk.glob('*.dll')),here/'main.c',here/'build-native.py',out/'switch.ld']},
 'nro_sha256':hashlib.sha256((out/'celeste64-switch.nro').read_bytes()).hexdigest()}
(out/'nativeaot-link.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Keep symbols and build identity together before the next generated build
# replaces them. Generated build artifacts are excluded from source control.
archive=root/'artifacts/nativeaot-builds'/manifest['nro_sha256']
archive.mkdir(parents=True,exist_ok=True)
for file in (out/'celeste64-switch.nro',out/'celeste64-switch.elf',
             out/'build/celeste64-switch.map',out/'nativeaot-link.json',
             out/'build-options.json',managed/'stage.json',managed/'compile-manifest.json',obj):
    shutil.copy2(file,archive/file.name)
print(out/'celeste64-switch.nro')
