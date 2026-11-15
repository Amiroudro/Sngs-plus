# Sarangsho Plus

An AI-assisted, Bangla-first news and knowledge platform for Bangladesh and the world, with a competitive-exam learning layer.

## Repositories

- **Private application source:** `Amiroudro/Sngs-plus`
- **Public edition archive and intended static Pages target:** `Amiroudro/sarangsho-plus-editions`
- **News engine:** `engine-v2/`

## Current capabilities

- Astro frontend with Today briefing and structured exam-learning panels.
- Published edition JSON archive with English editions and Bangla overlays.
- Bangla-first rendering. Static mode never substitutes English story summaries or learning text when a Bangla overlay is missing.
- Automatic edition sync from the public archive at 08:00 and 18:00 Asia/Dhaka.
- Static deployment workflow publishes only the built website and public edition files, not the private application source.

## Deployment setup

See [docs/INTEGRATION_STATUS.md](docs/INTEGRATION_STATUS.md). The GitHub Pages deployment workflow requires the private repository Actions secret `PAGES_DEPLOY_TOKEN` and Pages enabled on the public edition repository's `gh-pages` branch.

## Local development

Requires Node.js 22+.

```bash
cd frontend
npm install
npm run dev
```

The optional FastAPI backend is in `backend/`. GitHub Pages cannot host that Python service. The static Today page reads the published edition JSON files directly; metadata archive search requires the optional API.

## Editorial and rights safeguards

The 50-publication directory is a candidate list, not 50 active or rights-cleared integrations. Publisher terms, robots rules, paywalls, and reuse permissions must be checked individually. Automated structural checks are not factual verification. Backfilled editions may carry unresolved fact-check and rights-review notes; do not represent them as independently reverified.

See [docs/CONTENT_STANDARD.md](docs/CONTENT_STANDARD.md), [docs/SOURCE_DIRECTORY.md](docs/SOURCE_DIRECTORY.md), and [engine-v2/INTEGRATION_STATUS.md](engine-v2/INTEGRATION_STATUS.md).
