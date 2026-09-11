#!/usr/bin/env bash
# Experimental managed NativeAOT compilation only; this does not build an NRO.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
source "$here/../compat-v120/optimized-env.sh"
python3 "$here/prepare.py"
output="$root/artifacts/celeste64-nativeaot-managed"
dotnet publish "$output/managed/Game/Celeste64.Switch.csproj" \
  -c Release -r linux-arm64 --self-contained \
  -p:PublishAot=true -p:NativeLib=Static -p:IlcPackageVersion=9.0.3 \
  -p:RuntimeFrameworkVersion=9.0.3 -p:IlcOptimizationPreference=Speed \
  -p:StripSymbols=false -p:TrimmerSingleWarn=false \
  > "$output/publish.log" 2>&1
python3 "$here/check-output.py"
