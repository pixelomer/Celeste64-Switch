#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
mono="$root/third_party/upstream/mono-nx"
export MONO_NX_ROOT="$mono/dotnet_runtime"
export ICU_NX_INSTALL_DIR="$mono/icu/libnx"
export PATH="$PATH:$DEVKITPRO/devkitA64/bin"
bash "$here/bootstrap-shaders.sh"
python3 "$here/prepare.py"
cd "$root/artifacts/celeste64-switch-v120-bootstrap"
dotnet build managed/Game/Celeste64.Switch.csproj -c Release > logs/managed-build.log 2>&1
illink="$MONO_NX_ROOT/artifacts/bin/Mono.Linker/Debug/net9.0/illink.dll"
cfg="$MONO_NX_ROOT/src/mono/System.Private.CoreLib/src/ILLink"
rm -rf output
rm -f romfs/*.dll
dotnet "$illink" -x "$cfg/ILLink.Descriptors.xml" -x "$cfg/ILLink.LinkAttributes.xml" \
 --feature System.Resources.UseSystemResourceKeys true \
 -d "$MONO_NX_ROOT/artifacts/bin/mono/libnx.arm64.Debug" \
 -d "$MONO_NX_ROOT/artifacts/bin/runtime/net9.0-libnx-Debug-arm64" \
 -d managed/Game/bin/Release/net9.0 --trim-mode link \
 -a managed/Game/bin/Release/net9.0/Celeste64.Switch.dll all \
 --action copy Foster.Framework --action copy SharpGLTF.Core --action copy SharpGLTF.Runtime \
 --action copy Sledge.Formats --action copy Sledge.Formats.Map > logs/linker.log 2>&1
compiler="$MONO_NX_ROOT/artifacts/bin/mono/linux.x64.Debug/cross/linux-x64/libnx-arm64/mono-aot-cross"
: > logs/aot.log
for dll in output/*.dll; do
 echo "AOT $dll"
 "$compiler" --optimize=aggressive-inlining --path=output/ \
 --aot=full,static,direct-icalls,direct-pinvoke,ntrampolines=65536,nrgctx-trampolines=32768,nimt-trampolines=4096,ngsharedvt-trampolines=8192,tool-prefix=aarch64-none-elf- \
 "$dll" >> logs/aot.log 2>&1
done
cp output/*.dll romfs/
cp "$ICU_NX_INSTALL_DIR/share/icu/77.1/icudt77l.dat" romfs/
sed -n "s/Linking symbol: '\([^']*\)'\./STATIC_MONO_SYM(\1);/p" logs/aot.log > source/mono_symbols.h
make -j4 > logs/native-build.log 2>&1
cp celeste64-switch.nro celeste64-v120-dev.nro
sha256sum celeste64-v120-dev.nro > SHA256SUMS
