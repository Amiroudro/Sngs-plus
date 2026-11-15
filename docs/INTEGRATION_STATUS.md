# Deployment and integration status

Updated: 2026-11-16

## Current architecture

- Application source: private repository `Amiroudro/Sngs-plus`.
- Edition archive: public repository `Amiroudro/sarangsho-plus-editions`.
- Scheduled edition import: GitHub Actions at 08:00 and 18:00 Asia/Dhaka.
- Static frontend: Astro, built from `frontend/`.
- Static edition mode: the Today page reads the published edition index and JSON files from the deployed site's `/editions/` directory. Bangla mode requires a matching Bangla overlay and does not substitute English summaries or learning text.
- Intended public Pages target: `Amiroudro/sarangsho-plus-editions`, `gh-pages` branch.

## Deployment workflow

`.github/workflows/deploy-pages.yml` builds the Astro site whenever frontend code or synced edition data changes. It copies only the built static site and public edition JSON files to the Pages branch of the public edition repository. It does not publish the private source tree.

The workflow requires a repository Actions secret named `PAGES_DEPLOY_TOKEN`. The token must be a fine-grained personal access token restricted to `Amiroudro/sarangsho-plus-editions` with Contents: Read and write. The target repository's Pages settings must be configured to deploy from the `gh-pages` branch (root).

## What is and is not live

- The edition-sync workflow has previously completed successfully and imported the 1–15 November 2026 archive.
- The deploy workflow is configured in source, but a successful live deployment cannot be claimed until the required secret is added and the target repository Pages settings are enabled.
- GitHub Pages serves static files only. The Today page therefore has a static-edition mode. The metadata archive search remains unavailable without the optional FastAPI service.
- This deployment does not activate publisher scraping, grant reuse rights, independently fact-check backfilled stories, or generate new reporting. Source collection remains subject to publisher permissions and the engine's editorial/rights safeguards.

## One-time owner actions

1. Create a fine-grained token for the public edition repository with Contents read/write only.
2. Add it to the private app repository as Actions secret `PAGES_DEPLOY_TOKEN`.
3. In the public edition repository, open Settings → Pages and select Deploy from a branch → `gh-pages` → `/(root)`.
4. Run the `Build and deploy Sarangsho Plus to GitHub Pages` workflow.
