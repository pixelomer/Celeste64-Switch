# Shared selected optimization baseline.
export CELESTE64_V120_MESA_WORKER=1
export CELESTE64_V120_AOT_DEDUP=${CELESTE64_V120_AOT_DEDUP:-1}
export CELESTE64_V120_SPRITE_EMPTY=${CELESTE64_V120_SPRITE_EMPTY:-1}
export CELESTE64_V120_SPRITE_STREAM=${CELESTE64_V120_SPRITE_STREAM:-1}
export CELESTE64_V120_SPRITE_CHUNK=${CELESTE64_V120_SPRITE_CHUNK:-1}
export CELESTE64_V120_RUNTIME_CONTENT=${CELESTE64_V120_RUNTIME_CONTENT:-1}
export CELESTE64_V120_ASSET_QUEUE=${CELESTE64_V120_ASSET_QUEUE:-1}
export CELESTE64_V120_OPTIMIZATIONS=spatial,late,frustum,collision,gridwalk,snow,snowphase,material,materialrefs,uniforms,glcache,textures,imagebytes,animation,sprites,spritefill,spritefields,snowsprite,snowfill,modelsort,renderprep,rendermath,nativemath,mathunroll,matrixpair,stagebindings,nativeuniformcopy,shadowcache,drawableframe,hair,hairmesh,nativehair,nativecull,modelbits,skinbindings,uniformrefs,animationmath,indexedcurves,morphneutral,nativeskin,affinemath,posematrix,srtmatrix,stagefast,submitbatch,inflatedcull,stagecopybatch,leafinterop,spikemesh,posereuse
