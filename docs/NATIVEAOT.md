# NativeAOT build

The default build command selects NativeAOT and creates the NativeAOT SD-card
package. The runtime is a separate dependency rather than a Linux NuGet runtime
pack. Supply a compatible source-built Horizon .NET 9 runtime with the required
managed SDK libraries and native archives.

Required runtime support includes shared zero-filled BCL and GC mappings,
registered-thread GC suspension and ordering, native thread reaping, managed
Horizon path handling, static delegate thunks and a hardware-exception bridge.
Linux runtime archives and Linux libc or TLS assumptions are unsuitable.

With that runtime built:

```sh
./build.sh --nativeaot-runtime /path/to/horizon-runtime --fmod-dir /path/to/fmod-archives
```

The runtime needs the NativeAOT runtime and native-library Release subsets for
ARM64 Horizon, together with compatible ICU data. The managed SDK must provide
CoreLib, DisabledReflection, Reflection.Execution, StackTraceMetadata and
TypeLoader. Follow the runtime's version-pinned build recipe.

The managed stage compiles Celeste64 1.2.0 and its complete FMOD 2.02.18 API
with .NET 9.0.3 NativeAOT. Linux ARM64 is used only as an intermediate
code-generation target. A matching Horizon runtime, managed SDK libraries and
native launcher are required for the final link.

Run `bash src/celeste64-switch/nativeaot/build-managed.sh` for the compilation
stage and `python3 src/celeste64-switch/nativeaot/tests/run.py` for the host model
parsing and metadata test after dependencies have been prepared. The object
verifier requires the native imports and rejects IL trimming or AOT warnings.

SharpGLTF 1.0.5 Core is built from pinned source. Narrow changes remove unused
JSON reflection roots and replace diagnostic property reflection with typed
LogicalIndex access. JSON extras, extension data and deep cloning are retained.

Managed compilation uses ILC `--noinlinetls` and rejects direct TPIDR_EL0
thread-static accesses or TLS relocations in the generated object. Horizon uses
libnx software TLS, so the runtime helper path is retained.

The native stage links the managed object against the source-built Horizon
runtime and BCL archives. Set `NATIVEAOT_RUNTIME_ROOT` for both managed and native
stages; `ICU_NX_INSTALL_DIR` can select a compatible Horizon ICU installation.

The launcher retains ICU, TLS, GC and native workers until process exit. The
full FMOD backend and renderer remain unchanged. Compiler and linker metadata
are generated locally alongside other ignored build outputs.

## Optimization decisions

The production optimizations remain enabled. Controlled comparisons showed
that simplified variants could retain the target frame rate in stationary
scenes while substantially increasing update and render cost. Disabling selected
caches and batching also increased allocation by orders of magnitude, so those
optimizations remain part of the release configuration.

These comparisons guide the release configuration without claiming general
performance across every scene. NativeAOT supplies its own optimizing backend,
while the existing renderer and interop optimizations continue to cover other
costs.
