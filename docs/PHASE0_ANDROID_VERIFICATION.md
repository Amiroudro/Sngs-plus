# Phase 0 Android verification contract

This document records the release-verification gate for the existing Flutter client. It does not authorize a production release or modify the published-editions repository.

## Immutable application identity

- Android application ID / package: `com.sarangsho.plus`
- Keep the existing release keystore, signing configuration, versioning policy, and launcher identity unchanged.
- CI release APKs are unsigned-key fallback inspection artifacts only. They must never be distributed as production-signed updates.

## Reproducible CI toolchain

- Java: 17
- Flutter: 3.35.7 stable
- Android Gradle Plugin: 8.9.2
- Gradle wrapper: 8.11.1
- Android CMake: 3.31.6

The Flutter pin and CMake installation match the existing Android Gradle configuration. Do not upgrade Gradle or AGP as a side effect of feature work.

## Required Android checks

The Android client is not verified until all of these complete successfully on the Phase 0 branch:

1. `flutter pub get`
2. Bundled edition-data validation
3. `flutter analyze --no-fatal-infos`
4. Full `flutter test` suite
5. `flutter build apk --release`
6. Upload and inspect the CI APK artifact

A passing analyzer is not a substitute for a passing test suite or a successful release build.

## Bengali translation approval boundary

Production loading remains fail-closed. A Bengali overlay is applied only when every story in the edition carries `translation_status: "approved"`. Values such as `needs_review` and `automated_checks_passed` are not approval.

UI regression tests that need to exercise Bengali rendering may inject a clearly identified test-only fixture. Such fixtures must not change production JSON, mark archived translations approved, or weaken the loader's approval gate. Archive-wide Bengali checks must inspect only translations that are actually available to the runtime, or separately validate draft content without treating it as displayable.

## Published editions boundary

`Amiroudro/sarangsho-plus-editions` remains untouched by this Phase 0 Android verification branch. Its open compatibility PR is a separate dependency and must be reviewed independently. No published edition is deleted, overwritten, or re-published by these Android test changes.
