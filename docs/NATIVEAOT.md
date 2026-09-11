# NativeAOT build

The managed stage compiles Celeste64 1.2.0 and its complete FMOD 2.02.18 API
with .NET 9.0.3 NativeAOT. Linux ARM64 is an intermediate code-generation
target; its runtime libraries cannot be used on Horizon. A matching source-built
Horizon runtime, managed SDK libraries and native launcher are required.

Run `bash src/celeste64-switch/nativeaot/build-managed.sh` for the compilation
stage and `python3 src/celeste64-switch/nativeaot/tests/run.py` for the host model
parsing and metadata test after dependencies have been prepared. The object
verifier requires the native imports and rejects IL trimming or AOT warnings.
These checks verify the compilation output but do not replace runtime integration
testing.

SharpGLTF 1.0.5 Core is built from pinned source. Narrow changes remove unused
JSON reflection roots and replace diagnostic property reflection with typed
LogicalIndex access. JSON extras, extension data and deep cloning are retained.

Managed compilation uses ILC `--noinlinetls` and rejects direct TPIDR_EL0
thread-static accesses or TLS relocations in the generated object. Horizon uses
libnx software TLS, so the runtime helper path is retained.

The native stage links the managed object against a compatible source-built
Horizon runtime and BCL archives. Set `NATIVEAOT_RUNTIME_ROOT` to that separate
runtime checkout for both managed and native stages, then run
`python3 src/celeste64-switch/nativeaot/build-native.py` after the managed stage.
Use the runtime's matching Horizon CoreLib and SDK libraries rather than Linux
runtime libraries. `ICU_NX_INSTALL_DIR` can select a compatible Horizon ICU
installation.

The launcher retains ICU, TLS, GC and native workers until process exit. The
full FMOD backend and renderer remain unchanged. Compiler and linker metadata
are generated locally alongside other ignored build outputs.
