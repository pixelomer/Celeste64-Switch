# Attribution and distribution boundaries

This repository is an unofficial fan port. It is not made or endorsed by the
Celeste team, Nintendo, FMOD, or the authors of its dependencies.

| Component | Authors / source | License or distribution basis |
| --- | --- | --- |
| Celeste 64 source and derived patches | Maddy Makes Games, Inc.; [EXOK/Celeste64](https://github.com/EXOK/Celeste64) | MIT for Source, with upstream exceptions; notice in licenses/Celeste64-MIT.txt |
| Celeste 64 content and IP | Maddy Makes Games and the credited game creators | Separate upstream content terms; fetched for builds, not committed here |
| Foster and derived code | Noel Berry / [FosterFramework](https://github.com/FosterFramework/Foster) | MIT; notice in licenses/Foster-MIT.txt |
| Mono-nx | [exelix11](https://github.com/exelix11/mono-nx) | MIT; notice in licenses/Mono-NX-MIT.txt |
| .NET runtime and libraries | .NET Foundation and contributors | MIT plus third-party notices; copies in licenses/ |
| ICU | Unicode and contributors | Unicode license; notice in licenses/Unicode-ICU.txt |
| Shared-object loader | Andy Nguyen, fgsfds and [hl2_nx contributors](https://github.com/NaGaa95/hl2_nx) | MIT; notice in licenses/Loader-MIT.txt |
| SharpGLTF | [vpenades and contributors](https://github.com/vpenades/SharpGLTF) | MIT; notice in licenses/SharpGLTF-MIT.txt |
| Sledge formats | [LogicAndTrick and contributors](https://github.com/LogicAndTrick/sledge-formats) | MIT; restored through NuGet |
| SPIRV-Cross | [Khronos Group and contributors](https://github.com/KhronosGroup/SPIRV-Cross) | Apache-2.0; notice in licenses/SPIRV-Cross-Apache-2.0.txt |
| Mesa, libdrm, SDL2, libnx and devkitPro components | Their respective upstream authors | Their individual open-source licenses; installed or fetched separately |
| FMOD Studio API | Firelight Technologies | FMOD SDK license; downloaded separately with an automatically created or supplied account, or supplied as local archives |
| Temporary email service | [mail.tm](https://mail.tm) | Used for automatic FMOD account email verification |
| FMOD download request flow | [pixelomer/Celeste-FMOD2/download-fmod.sh](https://github.com/pixelomer/Celeste-FMOD2/blob/main/download-fmod.sh) | The Python implementation adapts the automatic account creation, email verification and login/download API sequence |

The exact fetched revisions and archive hashes are in dependencies.json and the
Mesa build script. Original fetched copyright notices are preserved. Additional
notices from fetched dependencies and the FMOD SDK are included in the local
installation package. Derivative source files are allowed in the repository;
this does not extend their MIT licensing to game content or FMOD binaries.

The generated ZIP embeds Celeste content in the NRO and includes FMOD shared
libraries. Keep it for local installation unless you have the permissions required
by those licenses to distribute it. Publishing the source repository does not
publish the generated ZIP: dist/, artifacts/, downloads/, fmod/ and third_party/
are ignored. 
The optional menu icon is derived from the official itch.io banner or supplied
locally and remains subject to the game content terms.
