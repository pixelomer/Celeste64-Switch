#!/usr/bin/env bash
set -euo pipefail

# Recorded accepted set from the render audit. Set CELESTE64_OPTIMIZATIONS
# explicitly to build a comparison with individual flags omitted.
if [[ ! -v CELESTE64_OPTIMIZATIONS ]]; then
 export CELESTE64_OPTIMIZATIONS=spatial,late,frustum,material,collision,sprites,animation,uniforms,snow,renderprep,glcache,hair,textures,materialrefs,modelsort,hairmesh,rendermath,nativemath,nativehair,imagebytes,snowphase,gridwalk,imagelifetime,matrixbindings,skinbindings,animationmath,morphneutral,affinemath,spritefill,mathunroll,matrixpair,snowsprite
fi
export CELESTE64_AOT_OPTIMIZE=${CELESTE64_AOT_OPTIMIZE-aggressive-inlining}
export CELESTE64_BUILD_NAME=${CELESTE64_BUILD_NAME-celeste64-switch-fmod-release}
port_dir=$(cd "$(dirname "$0")" && pwd)
exec bash "$port_dir/build.sh"
