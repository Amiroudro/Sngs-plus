# Free-first operating model

## Target cost

The feature architecture should require no paid AI API, no paid database and no always-on server. This is a design target, not a guarantee of unlimited free hosting or bandwidth.

## Components

| Need | Choice |
|---|---|
| Source control | Existing GitHub repositories |
| News processing | Existing Python Engine v2 |
| Data validation | Python tests and schema validators |
| Static content distribution | Public editions repository and GitHub Pages |
| Android client | Existing Flutter app |
| Website | Existing Astro site |
| Personal progress | Local device storage |
| Search | Precomputed bilingual index and local deterministic ranking |
| Charts | Flutter rendering from static indicator records |
| AI | Not required for the first release |

## GitHub Actions

- Reuse existing scheduled workflows rather than creating one workflow per feature.
- Avoid running Flutter release builds on every content update.
- Keep artifact retention short.
- Use a spending budget that prevents unexpected paid usage.
- Monitor included Actions minutes and storage.
- Scheduled workflow execution is not guaranteed to start at the exact minute; the app should also check the manifest when opened or refreshed.

## GitHub Pages and static files

GitHub Pages is suitable for the public JSON distribution model, subject to repository/site size and bandwidth limits. It cannot run the Python engine or a persistent API server. The Python engine runs in GitHub Actions or a local development environment; the app consumes static output.

Do not use public tile servers or free API endpoints in a way that violates their usage policies. Offline maps require properly licensed static geographic data or a provider that explicitly permits offline caching.

## Data sources and licences

- Prefer official statistical agencies and international institutions for indicators.
- Record the exact series, unit, reference period, retrieval date and licence/terms.
- Open datasets still require attribution and compliance with their terms.
- Wikidata's structured data is CC0, but time-sensitive claims should be checked against authoritative records.
- A public newspaper article is not automatically licensed for copying or full-text processing.
- Publisher permissions remain disabled until each source and permission scope is verified.

## Privacy

- No user account is required for local learning analytics.
- Do not upload reading history, quiz attempts, bookmarks or personal learning records.
- Provide user-controlled export and restore.
- Keep secrets, private source registries and credentials out of public JSON packages.

## Capacity limits and fallback

- Keep packages small and split by update frequency.
- Download only changed packages.
- Cache the last known-good version.
- If GitHub Pages or Actions is unavailable, the existing bundled edition and cached packages remain usable.
- If a source API is unavailable, retain the last verified dataset and display its retrieval date. Never silently label stale data as current.

## What must not be done

- Do not add Firebase, Supabase, a hosted vector database or a paid AI API just because a feature is called “AI”.
- Do not run live external requests for every screen render.
- Do not rely on a public free API without checking rate limits, caching rules and licensing.
- Do not publish personal learner data.
- Do not activate newspaper collection because a source appears in a candidate list.
