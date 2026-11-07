# Sarangsho Plus

An AI-assisted, bilingual (English/Bangla) news and knowledge platform focused on Bangladesh and the world.

## Project status

**Foundation stage.** This repository starts with a mobile-first Astro website and a small Python API foundation. The newspaper collectors and AI editorial pipeline are planned next; no source is represented as connected until a working collector is implemented and tested.

## Product principles

- Original, concise summaries with clear links and attribution to publishers.
- Separate reported facts, background context, and AI-generated explanation.
- English and Bangla reading modes.
- Importance based on public impact and significance, not clicks alone.
- Respect publisher terms, robots.txt, paywalls, and copyright. Never bypass access controls or republish full articles.
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

The initial API exposes `/health` and a small demo endpoint. It does not yet collect live newspaper articles.

## Initial publishers to evaluate

- The Daily Star
- Dhaka Tribune
- The Financial Express
- New Age

Feed availability and article extraction must be checked publisher by publisher. RSS feeds may contain only excerpts or metadata.

## Roadmap

1. Foundation: responsive bilingual website, API skeleton, database schema.
2. Collection: feed discovery, safe article extraction, source monitoring.
3. Editorial intelligence: classification, event clustering, importance scoring, fact extraction, bilingual summaries.
4. Reading experience: story pages, source comparison, search, timeline, archive.
5. Exam Desk and vocabulary, then exports and advanced features.

See `docs/EDITORIAL_POLICY.md` for editorial and source-handling rules.

## Configuration and secrets

Never commit API keys, tokens, passwords, or private credentials. Use environment variables and local `.env` files (ignored by Git). A ChatGPT or Claude subscription does not automatically include API usage.

## License

No license has been selected yet. All third-party article content remains the property of its respective publisher.
