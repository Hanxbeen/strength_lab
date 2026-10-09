#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE="$ROOT/apps/ios/RiveRuntimePackage"
ARCHIVE="${RIVE_RUNTIME_ARCHIVE:-/tmp/RiveRuntime.xcframework.zip}"
CHECKSUM="6912ebf2cb6b5b99cac9a255f7d205cf8edf59a22fbdacd561a36d3820cc9baa"
SOURCE="https://github.com/rive-app/rive-ios/releases/download/6.28.1/RiveRuntime.xcframework.zip"

if [ ! -f "$ARCHIVE" ]; then
    echo "Downloading official RiveRuntime 6.28.1..."
    curl -fL --retry 3 --connect-timeout 15 -C - -o "$ARCHIVE" "$SOURCE"
fi

ACTUAL="$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')"
if [ "$ACTUAL" != "$CHECKSUM" ]; then
    echo "SHA256 mismatch. Expected $CHECKSUM, got $ACTUAL" >&2
    exit 1
fi

mkdir -p "$PACKAGE/Binaries"
if [ ! -d "$PACKAGE/Binaries/RiveRuntime.xcframework" ]; then
    echo "Extracting signed official XCFramework..."
    unzip -q "$ARCHIVE" -d "$PACKAGE/Binaries"
fi
test -f "$PACKAGE/Binaries/RiveRuntime.xcframework/Info.plist"
echo "RiveRuntime 6.28.1 verified and installed locally."
