#!/usr/bin/env bash
# Release build gate (Phase 5).
#
# Runs BOTH edition validators BEFORE any build, then analyze, tests
# and the split-per-ABI release build:
#   1. python3 ../tools/validate_editions.py  (repo-root data gate)
#   2. dart tools/validate_bangla.dart        (Phase 4 Bengali gate)
# Either validator failing — or missing — stops the build here
# (set -e): a bad edition can never ship, and a missing validator
# file fails closed instead of silently skipping the check.
#
# This script is the PRIMARY gate (it is what the build agent runs).
# android/app/build.gradle also has a `validateEditions` Gradle task
# hooked to preReleaseBuild as a backstop, so a direct
# `flutter build apk --release` is gated too.
#
# Build-environment notes (see app/BUILD_NOTES.md §11): the Gradle
# daemon needs IPv4 loopback on this VM, and flutter/dart live at
# ~/tools/flutter/bin (added to PATH here when absent).
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v flutter >/dev/null 2>&1; then
  if [ -x "$HOME/tools/flutter/bin/flutter" ]; then
    export PATH="$HOME/tools/flutter/bin:$PATH"
  fi
fi

export GRADLE_USER_HOME="${GRADLE_USER_HOME:-/home/hatch/.gradle}"
export JAVA_TOOL_OPTIONS="-Djava.net.preferIPv4Stack=true"
export GRADLE_OPTS="-Djava.net.preferIPv4Stack=true"

echo "== Phase 5 gate: edition validator =="
# Lives at the REPO root (tools/validate_editions.py), run from there.
python3 ../tools/validate_editions.py
echo "== Phase 4 gate: Bengali validator =="
dart tools/validate_bangla.dart
echo "== version sync: pubspec vs app_update_service =="
pubspec_code=$(grep -oE '^version: .*\+[0-9]+' pubspec.yaml | grep -oE '[0-9]+$')
service_code=$(grep -oE 'currentVersionCode = [0-9]+' lib/services/app_update_service.dart | grep -oE '[0-9]+$')
if [ "$pubspec_code" != "$service_code" ]; then
  echo "MISMATCH: pubspec +$pubspec_code vs app_update_service $service_code"
  echo "Keep lib/services/app_update_service.dart currentVersionCode in sync with pubspec.yaml."
  exit 1
fi
echo "version code $pubspec_code in sync"
echo "== analyze =="
flutter analyze
echo "== tests =="
flutter test
echo "== release build (split per ABI) =="
flutter build apk --release --split-per-abi
echo "== OK: release APKs in build/app/outputs/flutter-apk/ =="
