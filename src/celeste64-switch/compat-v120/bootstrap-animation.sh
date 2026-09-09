#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
source_dir="$root/third_party/upstream/sharpgltf-1.0.5"
revision=4b28af2b6e5e30c6bade3f8baaf6b5e1a67ceb98
if [[ ! -d "$source_dir/.git" ]]; then
 git clone --filter=blob:none --no-checkout https://github.com/vpenades/SharpGLTF.git "$source_dir"
 git -C "$source_dir" checkout --detach "$revision"
fi
[[ $(git -C "$source_dir" rev-parse HEAD) == "$revision" ]]
git -C "$source_dir" diff --exit-code "$revision" --
