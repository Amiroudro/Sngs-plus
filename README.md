# Sarangsho Plus

An AI-assisted, bilingual (English/Bangla) news and knowledge platform focused on Bangladesh and the world, with a study layer for BCS, Bangladesh Bank and other competitive examinations.

## Project status

**Foundation stage.** The repository contains a mobile-first Astro website, a small Python API foundation and a SQLite schema. The homepage is a transparent product preview, not a live news feed. No newspaper collection or AI editorial pipeline is yet connected to the live site.

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

The initial API exposes `/health` and `/api/v1/briefing`. The briefing endpoint currently returns an empty list with a demo status.

## Initial publishers to evaluate

The database currently contains four disabled starter publishers: The Daily Star, Dhaka Tribune, The Financial Express and New Age. These entries are not connected feeds. Feed URLs, permitted access methods and publisher terms must be verified individually before enabling collection.

A wider candidate source directory can be added after the list has been checked for current publication status, language, access terms, feed availability and regional coverage. A candidate directory must never be presented as 50 live integrations.

## Roadmap

1. Foundation: responsive bilingual website, API skeleton, database schema and editorial standards.
2. Collection: source registry, feed discovery, safe metadata ingestion and source monitoring.
3. Editorial intelligence: event clustering, importance scoring, fact extraction, verification and bilingual summaries.
4. Study layer: vocabulary, exam-linked questions, revision notes and cumulative review.
5. Reading experience: source comparison, search, timeline, archive and exports.

## Configuration and secrets

Never commit API keys, tokens, passwords or private credentials. Use environment variables and local `.env` files (ignored by Git). A ChatGPT or Claude subscription does not automatically include API usage.

## License

No license has been selected yet. All third-party article content remains the property of its respective publisher.
