# syntax=docker/dockerfile:1

# Keep the host toolchain separate from the source tree. The checkout is mounted
# at /work when the image is run, so downloaded SDKs and release outputs never
# become Docker image layers.
FROM python@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254 AS python
# Mesa 20.1 still imports distutils; setuptools supplies its Python 3.12
# compatibility implementation.
RUN python -m pip install --no-cache-dir \
      Mako==1.3.10 \
      Pillow==11.3.0 \
      setuptools==80.9.0

FROM mcr.microsoft.com/dotnet/sdk@sha256:20387c6674c30e46def0cc8cb557bd2a69b35afdf18c19c3694638d0a90897e4 AS dotnet9
FROM mcr.microsoft.com/dotnet/sdk@sha256:4ea6fe75dd36706bb6d8c3c293d4c4315840f5d76ea28ac97def77e3ec487fa5 AS dotnet10

FROM devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      bison \
      ca-certificates \
      cmake \
      flex \
      git \
      libicu72 \
      libssl3 \
      meson \
      ninja-build \
      openjdk-17-jdk-headless \
      patch \
      pkg-config \
 && rm -rf /var/lib/apt/lists/*

COPY --from=python /usr/local/ /usr/local/
COPY --from=dotnet9 /usr/share/dotnet/ /usr/share/dotnet/
COPY --from=dotnet10 /usr/share/dotnet/ /usr/share/dotnet/
RUN ln -s /usr/share/dotnet/dotnet /usr/local/bin/dotnet

ENV DEVKITPRO=/opt/devkitpro \
    DEVKITA64=/opt/devkitpro/devkitA64 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 \
    DOTNET_NOLOGO=1 \
    DOTNET_CLI_HOME=/tmp/dotnet-home \
    NUGET_PACKAGES=/work/downloads/nuget \
    HOME=/tmp \
    PATH=/opt/devkitpro/devkitA64/bin:/opt/devkitpro/tools/bin:/opt/devkitpro/portlibs/switch/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

WORKDIR /work
CMD ["./build.sh"]
