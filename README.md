# Celeste 64 for Nintendo Switch

> [!IMPORTANT]
> AI assistance was heavily used for this port. Most of the work was done by
> GPT-6 Astra. The produced code was not audited or verified by a human beyond
> running the compiled NRO on a real Nintendo Switch. Human maintainability or
> readability was not a goal for this project.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

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
If FMOD archives are missing, the downloader automatically creates and verifies an
FMOD account using [mail.tm](https://mail.tm), then downloads both SDKs. Generated
credentials are reused from the ignored, owner-only `fmod-login.json` file.
Alternatively, [download the SDKs manually](docs/BUILDING.md#fmod) and supply the
original FMOD Studio API 2.02.18 Linux and Android archives:

```sh
./build.sh --fmod-dir /path/to/fmod-archives
```

The result is `dist/celeste64-switch-1.2.0.zip`, with a SHA-256 checksum alongside it.
Extract the ZIP into the root of the SD card, merging the `switch` folder. Run
`Celeste 64` (`switch/celeste64/celeste64.nro`) from the Homebrew Menu in **full application mode** (hold R
while starting a game); Album/applet mode does not provide enough memory.
Input supports one player using a Pro Controller, paired Joy-Cons, or handheld
controls. Individual Joy-Cons and additional player controllers are not supported.
Saves, controls and logs live in `switch/celeste64/userdata`. Keep both FMOD shared
libraries under `switch/celeste64/fmod`. When upgrading an earlier 1.2.0 build,
[move its existing save directory](docs/BUILDING.md#upgrading-an-earlier-layout)
before launching; installation ZIPs never overwrite saves.

To embed your own existing 256x256 baseline JPEG menu icon, use
`./build.sh --icon /path/to/icon.jpg`. It is cached in ignored `local/icon.jpg`
for subsequent builds. Otherwise the build attempts to generate an icon from the
[itch.io GIF banner](https://maddymakesgamesinc.itch.io/celeste64), using optional
Python Pillow. If this fails, the build continues with the generic default icon.
Artwork is downloaded or supplied locally and is not tracked in Git.


## Source and licensing

Only port source, build scripts and documentation are tracked. Upstream checkouts,
assets, FMOD archives/libraries, credentials and generated packages are ignored.
Do not force-add these files or publish a build directory as source.

See [THIRD_PARTY.md](THIRD_PARTY.md) for upstream licenses and distribution boundaries.

- [Build requirements, dependency pins and troubleshooting](docs/BUILDING.md)
- [Optimization and compatibility notes](docs/OPTIMIZATIONS.md)
- [Third-party attribution](THIRD_PARTY.md)
