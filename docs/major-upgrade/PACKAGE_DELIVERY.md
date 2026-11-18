# Intelligence package delivery

## Goal

Extend the existing edition download/cache system without creating a second, inconsistent network stack.

The app already downloads edition indexes and JSON files, validates them and retains usable local content when the network is unavailable. Intelligence packages should use the same transport, retry, checksum and cache principles.

## Public repository layout

```text
sarangsho-plus-editions/
├── editions/
│   ├── index.json
│   ├── data-YYYY-MM-DD.json
│   └── bn-YYYY-MM-DD.json
└── intelligence/
    ├── manifest.json
    ├── stories/
    │   ├── index.json
    │   └── event-or-story-records/
    ├── timelines/
    │   └── index.json
    ├── perspectives/
    │   └── index.json
    ├── questions/
    │   ├── daily/
    │   └── bank/
    ├── knowledge/
    │   ├── entities.json
    │   └── relationships.json
    ├── world/
    │   ├── countries.json
    │   ├── organizations.json
    │   └── events/
    ├── indicators/
    │   ├── catalog.json
    │   └── country-series/
    └── search/
        ├── index-bn.json
        └── index-en.json
```

Do not place every story, question, entity and observation in one giant JSON file. Split by feature and update frequency.

## Manifest contract

```json
{
  "manifest_schema": 1,
  "content_version": "2026-11-18.1",
  "generated_at": "2026-11-18T12:00:00+06:00",
  "minimum_app_version": "1.4.0",
  "packages": [
    {
      "package_id": "questions.daily.2026-11-18",
      "path": "intelligence/questions/daily/2026-11-18.json",
      "schema_version": 1,
      "language": "multi",
      "bytes": 12345,
      "sha256": "..."
    }
  ]
}
```

The sample byte count and digest are placeholders. The exporter must calculate the actual values.

## Update algorithm

1. Fetch the manifest over HTTPS.
2. Validate manifest schema and minimum app version.
3. Compare package IDs, versions and SHA-256 digests with the local manifest.
4. Download only changed packages.
5. Write to a temporary file, never directly over the current working package.
6. Verify exact byte size and SHA-256.
7. Parse JSON and validate its schema and internal references.
8. Atomically promote the new file and manifest.
9. Keep the previous known-good package until the new package is fully accepted.
10. If any step fails, continue using the last known-good version and report the failed update.

## Offline behaviour

- Daily editions and previously downloaded intelligence remain readable offline.
- A missing package does not crash unrelated screens.
- Search indexes are optional enhancements; basic story reading must still work if an index is unavailable.
- A failed update never deletes the last working package.
- A package version can be rolled back by publishing a previous known-good manifest.

## Integration with current code

- Extend `EditionDownloadService` or extract a shared `ContentPackageService` from it.
- Reuse its HTTP client and local cache path conventions.
- Keep edition-specific parsing in the existing loader.
- Add a package registry so screens request only the package they need.
- Do not duplicate update polling in every screen.

## Static website

The Astro website consumes the same public JSON package files. It does not need to call the FastAPI backend for every page view. The website should validate the manifest during build and fail if a required package is missing or malformed.

## Integrity and security

- SHA-256 checks detect corruption, not malicious publishers. The publishing repository and CI remain trusted release boundaries.
- Never put secrets, private rights records, user progress or account data in the public package.
- Do not embed arbitrary executable code in package JSON.
- Enforce size limits before parsing.
- Validate URLs and source references.
