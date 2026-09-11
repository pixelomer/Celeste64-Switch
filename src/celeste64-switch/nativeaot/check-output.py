"""Validate and record the managed compilation stage, without claiming a port."""
import hashlib, json, re, struct, subprocess
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parents[2]
out=root/'artifacts/celeste64-nativeaot-managed'
log=(out/'publish.log').read_text()
warnings=re.findall(r'warning (IL\d+):[^\n]+',log)
if warnings:raise SystemExit('AOT/trimming warnings remain: '+', '.join(sorted(set(warnings))))
obj=out/'managed/Game/obj/Release/net9.0/linux-arm64/native/Celeste64.Switch.o'
header=obj.read_bytes()[:64]
if header[:6]!=b'\x7fELF\x02\x01' or struct.unpack_from('<HH',header,16)!=(1,183):
    raise SystemExit('Expected a fresh AArch64 ELF relocatable object')
symbols=subprocess.check_output(['aarch64-none-elf-nm','-g','--defined-only',str(obj)],text=True)
if not re.search(r'\bT C64ManagedMain$',symbols,re.M):raise SystemExit('Managed entry point is missing')
imports=subprocess.check_output(['aarch64-none-elf-nm','-u',str(obj)],text=True)
assembly=subprocess.check_output(['aarch64-none-elf-objdump','-dr',str(obj)],text=True)
if re.search(r'\btpidr_el0\b|R_AARCH64_TLS',assembly,re.I):
    raise SystemExit('Linux TLS instructions/relocations remain in the game object')
for name in ('C64AudioInit','C64AudioShutdown','C64AudioUpdate','C64AudioLoad','FosterStartup'):
    if not re.search(r'\bU '+name+r'$',imports,re.M):raise SystemExit('Native import missing: '+name)
manifest=json.loads((out/'stage.json').read_text())
manifest.update(object_sha256=hashlib.sha256(obj.read_bytes()).hexdigest(),
                object_bytes=obj.stat().st_size,il_warnings=0,direct_linux_tls_accesses=0,
                generated_sources={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sorted((out/'managed').rglob('*.cs'))
                                   if not {'obj','bin'}.intersection(p.relative_to(out).parts)})
(out/'compile-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'NativeAOT managed stage verified: {obj.stat().st_size} bytes, zero IL warnings; Horizon runtime still required.')
