# Building

## Administrator-provided dependencies

The supported host is Linux x86-64. The public Mono AOT SDK contains an x86-64
Linux compiler. Native Windows, macOS and ARM hosts are not supported by this
recipe. Use a Linux x86-64 installation or VM, with the repository on its Linux
filesystem. Repository, devkitPro and JDK paths must not contain whitespace,
because the upstream native Makefiles do not quote those paths consistently.

Install these before running the build; scripts do not invoke sudo or alter the
system package manager:

- devkitPro **devkitA64**, switch-tools, libnx **4.10.0 or newer**, and Switch
  portlibs: SDL2, Mesa, libdrm/nouveau, zlib and their dependencies. The
  `switch-dev` group plus `switch-sdl2`, `switch-mesa` and `switch-libdrm_nouveau`
  are the relevant devkitPro packages. Use devkitPro's supported package manager
  (`dkp-pacman` on its supported distributions) and its installation instructions:
  <https://devkitpro.org/wiki/Getting_Started>.
- devkitPro's Meson cross-compilation helpers (`meson-cross.sh` and its associated
  toolchain files), supplied by `dkp-meson-scripts`.
- .NET SDK **10** and SDK **9**. SDK 10 drives the build; SDK 9 supplies the net9.0
  reference pack. Follow <https://learn.microsoft.com/dotnet/core/install/linux>.
  `global.json` selects a .NET 10 feature band. NuGet restores the pinned package
  references in generated projects.
- Git, Python **3.12+**, Python Mako, CMake, Ninja, Meson, GNU Make, patch, GCC/G++,
  pkg-config and a JDK supplying JNI headers (JDK 17 or 21 is suitable).

For example, Debian/Ubuntu build utilities can be installed with
`apt install git python3 python3-mako cmake ninja-build meson build-essential patch pkg-config openjdk-21-jdk`.
The devkitPro and Microsoft SDK packages use their own documented repositories.
On Fedora the analogous utility packages include `python3-mako`, `ninja-build`,
`meson`, `cmake`, `gcc-c++`, `make`, `patch`, `pkgconf-pkg-config` and
`java-21-openjdk-devel`. Package availability depends on the distribution release.

Set `DEVKITPRO` if it is not `/opt/devkitpro`. `JAVA_HOME` may be set explicitly;
otherwise the build discovers it from `javac`. Run `python3 scripts/preflight.py`
to check dependencies without fetching or building anything. In particular,
older libnx releases are unsuitable for Horizon 21+ because of its TLS ABI change.
The tested toolchain is devkitA64 15.2.0, libnx 4.12.0 and .NET SDK 10.0.111.

## Dependency fetching

`dependencies.json` records exact Git revisions and archive SHA-256 digests.
`scripts/fetch.py` fetches these revisions into ignored `third_party/upstream/`.
It refuses to reset existing checkouts that have the wrong revision or tracked
local modifications. Fix or move such a checkout before retrying.

The recipe uses:

- Celeste 64 `6edfe1e`: game source and runtime content.
- Celeste 64 `bfc7a3b`: base native-backend preparation inputs. Generated game
  sources/content are subsequently replaced with the current-game inputs.
- Foster `a5b574f` for current managed API adaptation, and `351d206` (0.1.18)
  for the proven SDL2/OpenGL native backend.
- SharpGLTF `4b28af2` (1.0.5), with `5a33d54` for the base compatibility pipeline.
- Mono-nx `fec0577` and its **rel-3 Linux x64 SDK**, including the AOT compiler,
  runtime static libraries, linker tools, headers and full ICU 77.1 data.
- SPIRV-Cross `be71ee8` for GLSL conversion; hl2_nx `41e045e` for the MIT Android
  shared-object loader implementation.
- Checksum-pinned Mesa 20.1.0-rc3 and devkitPro Switch patches. The port builds its
  own Mesa archive with worker fixes; it does not modify the installed Mesa.

The Mono runtime is supplied by the upstream SDK download, rather than rebuilt
from the entire .NET runtime tree on every checkout. To rebuild that SDK itself,
follow the pinned mono-nx repository's `build_mono.sh`, `icu/build_icu.sh` and
`gather_sdk.sh`. SDK compatibility across arbitrary future devkitPro updates is
not guaranteed; retain the tested toolchain when reproducing a build.

All source checkout and SDK downloads have been exercised from an empty dependency
directory. Mesa and the game are built locally. This repository does not need a
commercial game dump, Nintendo SDK, console keys, or a pre-existing port build.

## FMOD

`scripts/download-fmod.sh` adapts the automatic registration, verification, login and download flow
from [pixelomer/Celeste-FMOD2](https://github.com/pixelomer/Celeste-FMOD2/blob/main/download-fmod.sh).
It requests **FMOD Studio API 2.02.18 for Linux and Android** from FMOD's servers
and verifies archive hashes. Linux supplies headers; Android supplies ARM64 shared
libraries. Both original archive layouts, including the nested Linux archive,
are handled. The Switch audio backend implements Android-compatible loading and
uses the homebrew audio service; no proprietary Switch FMOD SDK is required.

When either archive is missing, the default build creates a temporary mailbox
through [mail.tm](https://mail.tm), registers an FMOD account without subscribing
to newsletters, verifies its email, and downloads the pinned SDKs automatically.
Generated account credentials and registration progress are stored in the ignored
`fmod-login.json` at the repository root, with file permissions `0600`. Treat this
file as a secret: do not share or commit it. Passwords and tokens are never printed.
Later runs reuse the account; an interrupted verification resumes the same account.
The verification wait defaults to 180 seconds, after which the script exits.

To use your own account, provide both `FMOD_USERNAME` and `FMOD_PASSWORD` through
your secret environment. These override saved credentials and are not written to
disk. For an interactive password prompt without automatic registration, run:

```sh
./scripts/download-fmod.sh --existing-account
./build.sh
```

To **download manually**, sign in to your own account at the
[FMOD downloads page](https://www.fmod.com/download), choose **FMOD Studio API
2.02.18**, and download the **Linux** and **Android** SDK archives. Keep the original
archives, without extracting or renaming them, together in a directory:

- `fmodstudioapi20218linux.tar.gz`
- `fmodstudioapi20218android.tar.gz`

Then run:

```sh
./build.sh --fmod-dir /path/to/archives
```

Or import just the SDK archives before building:

```sh
./scripts/download-fmod.sh --archive-dir /path/to/archives
```

Manual archive import and verified cached archives require no account creation or
network access from the downloader. Already verified archives in `fmod/` are reused.
A checksum mismatch is a hard failure; do not disable verification to accept a
different API version. The downloader can also be run separately with
`--email-timeout 300` to extend the verification wait. Automatic registration and
downloads depend on FMOD and mail.tm availability; existing-account login and
manual archives remain alternatives if those services reject or change the flow.
The automatic account/verification/download flow and both pinned archive hashes
were verified with the live services on 2026-09-10.

## Outputs and installation

The release build creates `dist/celeste64-switch-1.2.0.zip` and its checksum.
The ZIP contains the release NRO, required FMOD libraries, license notices and
a deterministic build manifest. Generated sources and build outputs remain in
ignored directories.

Extract the ZIP into the root of the SD card and launch
`switch/celeste64/celeste64.nro` with the Homebrew Menu in full application mode.
The application stores saves under `switch/celeste64/userdata`.

An optional 256x256 baseline JPEG may be supplied with `--icon`; otherwise the
build can derive an icon from the official Celeste 64 itch.io banner.

## Verification and troubleshooting

Run `python3 -m unittest discover -s tests -v` for build-support checks.
Build logs separate managed compilation, linking, AOT and native compilation;
start with the failing stage's log. Unset custom experiment variables when using
lower-level scripts; the top-level release wrapper clears them automatically.
Changing a pinned upstream revision usually requires reviewing the patch anchors,
API adaptations and performance tests, rather than merely changing a version.
