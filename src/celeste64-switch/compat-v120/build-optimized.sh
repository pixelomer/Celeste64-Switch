#!/usr/bin/env bash
# Reproduce the selected current-game candidate. build.sh remains the lower-level entry point.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
export CELESTE64_V120_MESA_WORKER=1
export CELESTE64_V120_RUNTIME_CONTENT=${CELESTE64_V120_RUNTIME_CONTENT:-1}
export CELESTE64_V120_ASSET_QUEUE=${CELESTE64_V120_ASSET_QUEUE:-1}
export CELESTE64_V120_OPTIMIZATIONS=spatial,late,frustum,collision,gridwalk,snow,snowphase,material,materialrefs,uniforms,glcache,textures,imagebytes,animation,sprites,spritefill,spritefields,snowsprite,snowfill,modelsort,renderprep,rendermath,nativemath,mathunroll,matrixpair,stagebindings,nativeuniformcopy,shadowcache,drawableframe,hair,hairmesh,nativehair,nativecull,modelbits,skinbindings,uniformrefs,animationmath,indexedcurves,morphneutral,nativeskin,affinemath,posematrix,srtmatrix,stagefast,submitbatch,inflatedcull,stagecopybatch,leafinterop,spikemesh,posereuse
exec bash "$here/build.sh"
