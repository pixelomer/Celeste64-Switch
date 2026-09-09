#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
source_dir="$root/third_party/upstream/spirv-cross"
build_dir="$root/artifacts/spirv-cross-build"
revision=be71ee8c12cd7dc5ca8fa9581f708c2e8561fe2a
if [[ ! -d "$source_dir/.git" ]]; then
 git clone https://github.com/KhronosGroup/SPIRV-Cross.git "$source_dir"
 git -C "$source_dir" checkout --detach "$revision"
fi
[[ $(git -C "$source_dir" rev-parse HEAD) == "$revision" ]]
git -C "$source_dir" diff --exit-code "$revision" --
if [[ -x "$build_dir/spirv-cross" && -f "$build_dir/pinned-source.txt" ]] &&
   [[ $(cat "$build_dir/pinned-source.txt") == "$revision" ]]; then
 exit 0
fi
cmake -S "$source_dir" -B "$build_dir" -DCMAKE_BUILD_TYPE=Release \
 -DSPIRV_CROSS_ENABLE_TESTS=OFF -DSPIRV_CROSS_ENABLE_CPP=ON \
 -DSPIRV_CROSS_ENABLE_HLSL=ON -DSPIRV_CROSS_ENABLE_MSL=ON
cmake --build "$build_dir" -j4
printf '%s\n' "$revision" > "$build_dir/pinned-source.txt"
