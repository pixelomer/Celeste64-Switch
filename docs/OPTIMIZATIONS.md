# Compatibility and performance

## Runtime and graphics

The port retargets the current game to .NET 9 for Mono-nx and compiles every
managed assembly with full AOT and aggressive inlining. Repeated generic native
code is collected into one registered `aot-instances` image. This is code
sharing at build time, not an interpreter or JIT fallback. It substantially
reduces the executable while retaining the optimized hot paths. Full ICU data
and localization support remain enabled.

A compatibility layer connects the current Foster-facing game code to the
older SDL2/OpenGL native backend. Shader conversion uses pinned SPIRV-Cross.
The current game content, mechanics and visual effects are preserved. Changes
to the frame clock preserve fixed-step simulation and handle long pauses without
an unbounded catch-up loop.

The selected Mesa patch enables its GL worker and keeps it on CPU 1. The main
thread submits ordered graphics commands while the worker executes them. Context
and drawable changes explicitly drain queued references before their resources
are destroyed. Complete Mesa archives are rebuilt together; mixing individual
objects from incompatible Mesa builds is avoided.

## Main optimizations

| Area | Work removed or reduced | Behavior preserved |
| --- | --- | --- |
| Spatial/collision queries | Broad-phase cell traversal, reusable scratch storage, early geometric rejection and specialized ray/wall math | Original narrow-phase decisions and iteration requirements |
| Animation and skinning | Cached indexed curves and joint bindings, immutable pose reuse, neutral morph shortcuts, native affine/SRT/skin calculations | Interpolation, transforms, animation timing and vertex results |
| Rendering preparation | Cached material/uniform references, drawable preparation, conservative bounds, sorted model lists and point-shadow reuse | Visibility, draw order, transforms and shadow results |
| Draw submission | Batched state/uniform transfer, redundant GL state removal and native copies of known matrix layouts | Submitted values and ordering |
| Sprites and snow | Direct vertex filling, cached field access and pass preparation, empty-pass removal | Particle behavior, sprite geometry, colors and ordering |
| Sprite upload synchronization | Fresh storage for complete vertex replacement and ordered chunks up to 32,704 bytes | Exact bytes and offsets before the following draw |
| Hair and repeated meshes | Reused buffers and native hair math, cached spike geometry | Existing shapes, animation and collision behavior |
| Audio scheduling | Prefer CPU 2 within the existing worker affinity mask | FMOD events, banks, sample settings and audio timing |
| Startup | Bounded asset-read preparation and omission of editor-only source/backup content | Runtime assets, parsing/validation and full ICU |

The upload change addresses a specific driver boundary: normal sprite payloads
of roughly 44–58 KB exceeded Mesa's 32 KiB marshalled-command limit and forced
synchronization. Empty uploads could also enter a synchronous fallback. Complete
sprite replacements now use fresh storage and ordered chunks reserving 64 bytes
for command overhead. Other meshes and partial writes retain the original path.

FMOD uses the Android ARM64 2.02.18 libraries, loaded through an adapted MIT
shared-object loader and a narrow compatibility layer. Homebrew audio output
handles recoverable submission errors and pause/resume; an unavailable audio
service is not allowed to corrupt buffers or terminate the process through an
unhandled native callback. The libraries and game banks themselves are unchanged.

## Build organization

`src/celeste64-switch/prepare.py` generates the proven base backend and common
optimizations. `compat-v120/prepare.py` applies the current-game adaptations and
selected additional optimizations. Generated copies live under `artifacts/`,
so fetched upstream checkouts remain unchanged. Patch anchors and exact revision
checks fail explicitly when upstream changes invalidate an assumption.

