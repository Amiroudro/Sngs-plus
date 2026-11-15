# Sarangsho Plus

An AI-assisted, bilingual (English/Bangla) news and knowledge platform focused on Bangladesh and the world, with a study layer for BCS, Bangladesh Bank and other competitive examinations.

## Project status

**Foundation + integration branch.** The `main` branch remains a foundation preview. The open Engine v2 integration PR imports the tested pipeline source and adds a read-only edition API that serves only human-published files indexed under `editions/`. No live newspaper collection is enabled, and no stories are auto-published.

The current content inventory and renovation scope are documented in [the content audit](docs/CONTENT_AUDIT.md). The rules for article summaries, fact verification, exam relevance, vocabulary and questions are in [the content standard](docs/CONTENT_STANDARD.md).

## Product principles

- Original, concise summaries with clear links and attribution to publishers.
- Separate reported facts, official claims, allegations, background context and AI-generated explanation.
- English and Bangla versions that preserve the same underlying facts.
- Importance based on public impact and significance, not clicks alone.
- Traceable facts, transparent uncertainty, corrections and human review for sensitive or disputed stories.
- Respect publisher terms, robots.txt, paywalls and copyright. Never bypass access controls or republish full articles.
- Free-first architecture, with AI provider integrations kept optional.

## Planned sections

Today · Topics · Exam Desk · Learn · Explore · Timeline · Saved · Archive

## Local development

### Website

Requires Node.js 22.12+.

```bash
cd frontend
npm install
npm run dev
```

### API

Requires Python 3.11+.

```bash
cd backend
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API exposes `/health`, `/api/v1/editions`, `/api/v1/editions/{YYYY-MM-DD}` and `/api/v1/briefing?language=en|bn`. It reads only files listed in the published edition index. With the initial empty index, the briefing correctly returns a demo status and no stories.

## Initial publishers to evaluate

The database currently contains four disabled starter publishers: The Daily Star, Dhaka Tribune, The Financial Express and New Age. These entries are not connected feeds. Feed URLs, permitted access methods and publisher terms must be verified individually before enabling collection.

A wider candidate source directory can be added after the list has been checked for current publication status, language, access terms, feed availability and regional coverage. A candidate directory must never be presented as 50 live integrations.

## Roadmap

1. Foundation: responsive bilingual website, API skeleton, database schema and editorial standards.
2. Collection: source registry, feed discovery, safe metadata ingestion and source monitoring.
3. Editorial intelligence: event clustering, importance scoring, fact extraction, verification and bilingual summaries.
4. Study layer: vocabulary, exam-linked questions, revision notes and cumulative review.
5. Reading experience: source comparison, search, timeline, archive and exports.

## Engine v2 integration

The pipeline source and integration limitations are documented in [`engine-v2/README.md`](engine-v2/README.md) and [`engine-v2/INTEGRATION_STATUS.md`](engine-v2/INTEGRATION_STATUS.md). The imported pipeline is not yet connected to automatic scheduling, the SQLite content model or the Astro frontend. Publishing still requires the engine's human-approval gate.

## Configuration and secrets

Never commit API keys, tokens, passwords or private credentials. Use environment variables and local `.env` files (ignored by Git). A ChatGPT or Claude subscription does not automatically include API usage.

## License

No license has been selected yet. All third-party article content remains the property of its respective publisher.
