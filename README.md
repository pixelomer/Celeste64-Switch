# Celeste 64 for Nintendo Switch

An unofficial homebrew port of **Celeste 64: Fragments of the Mountain**, based on
upstream commit `6edfe1e` (version 1.2.0). This is a fan port, not made or endorsed
by the Celeste team.

The build fetches pinned upstream sources, generates the compatibility and
optimization patches, compiles a fully AOT Mono executable, and creates an SD-card
installation ZIP. There is no JIT or interpreter fallback. Graphics, game mechanics,
audio and localization are preserved.

## Build

Use **Linux x86-64**, with the dependencies in [BUILDING.md](docs/BUILDING.md).
Then run:

```sh
./build.sh
```

The first build downloads sources, the pinned Mono/ICU SDK, and Mesa source inputs.
FMOD requires an existing account; the downloader prompts for your credentials
without saving them. Alternatively, supply the original FMOD Studio API 2.02.18
Linux and Android archives:

```sh
./build.sh --fmod-dir /path/to/fmod-archives
```

The result is `dist/celeste64-switch-1.2.0.zip`, with a SHA-256 checksum alongside it.
Extract the ZIP into the root of the SD card, merging the `switch` folder. Run
`celeste64-v120.nro` from the Homebrew Menu in **full application mode** (hold R
while starting a game); Album/applet mode does not provide enough memory.
Existing saves in `switch/celeste64-v120` are preserved. Keep both FMOD shared
libraries under `switch/celeste64/fmod`.


## Source and licensing

Only port source, build scripts and documentation are tracked. Upstream checkouts,
assets, FMOD archives/libraries, credentials and generated packages are ignored.
Do not force-add these files or publish a build directory as source.

See [THIRD_PARTY.md](THIRD_PARTY.md) for upstream licenses and distribution boundaries.

- [Build requirements, dependency pins and troubleshooting](docs/BUILDING.md)
- [Optimization and compatibility notes](docs/OPTIMIZATIONS.md)
- [Third-party attribution](THIRD_PARTY.md)
