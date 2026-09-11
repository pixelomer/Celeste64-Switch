#!/usr/bin/env bash
# Reproduce the selected current-game candidate. build.sh remains the lower-level entry point.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
source "$here/optimized-env.sh"
exec bash "$here/build.sh"
