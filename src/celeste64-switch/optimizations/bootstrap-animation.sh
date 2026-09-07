#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
destination="$root/third_party/upstream/sharpgltf-alpha0031"
revision=5a33d5452528d827ac55727f302d8a91a75c4186
if [[ ! -e "$destination" ]]; then
    git clone --no-checkout --filter=blob:none https://github.com/vpenades/SharpGLTF.git "$destination"
    git -C "$destination" checkout --detach "$revision"
fi
[[ $(git -C "$destination" rev-parse HEAD) == "$revision" ]]
