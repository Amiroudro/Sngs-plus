# Shared intelligence data contracts

**Status:** proposed schema; migration and exporter are not implemented yet.

The daily edition JSON remains the compatibility boundary for existing readers. New intelligence records are published as separate, versioned packages. The build-time SQLite schema is used for joins, validation and export; it is not the Android user's database.

## Existing structured foundation

The private repository already defines tables for:
- Sources and source routes.
- Articles, events and event/article links.
- Summaries, facts and fact evidence.
- Questions and answer options.
- Vocabulary items and occurrences.
- Review progress.
- Publisher rights reviews.
- Article localizations and exam assessments.

Migrations 001–003 extend this model. The current Engine v2 pipeline does not yet import every run into these tables. Implement an explicit importer and reconciliation tests before treating the database as live.

## Identifier rules

| Record | Stable identifier |
|---|---|
| Article | `article_uid`, assigned from a normalized canonical URL and persisted |
| Event | `event_uid`, registry-assigned and never recycled |
| Fact | `fact_uid`, stable within its evidence-backed claim |
| Entity | `entity_uid`, stable across spelling/alias changes |
| Relationship | `relationship_uid`, stable and independently reviewable |
| Question | `question_uid`, stable across editions and revisions |
| Indicator | `indicator_uid`, stable series definition |

Do not use collection-run IDs, array positions, display order or mutable headlines as permanent IDs. A URL hash is a useful article identity seed, but the importer must persist the chosen canonical identity and handle URL changes/redirects.

## Proposed migration 004

The exact SQL must be reviewed against the current schema before implementation. This is a design, not a migration file.

### Entities

```sql
CREATE TABLE entities (
  id INTEGER PRIMARY KEY,
  entity_uid TEXT NOT NULL UNIQUE,
  entity_type TEXT NOT NULL,
  canonical_name_en TEXT NOT NULL,
  canonical_name_bn TEXT,
  description_en TEXT,
  description_bn TEXT,
  source_refs_json TEXT NOT NULL DEFAULT '[]',
  review_status TEXT NOT NULL DEFAULT 'needs_review',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

### Aliases

```sql
CREATE TABLE entity_aliases (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL REFERENCES entities(id),
  language TEXT NOT NULL,
  alias TEXT NOT NULL,
  normalized_alias TEXT NOT NULL,
  UNIQUE(language, normalized_alias)
);
```

### Relationships

```sql
CREATE TABLE entity_relationships (
  id INTEGER PRIMARY KEY,
  relationship_uid TEXT NOT NULL UNIQUE,
  subject_entity_id INTEGER NOT NULL REFERENCES entities(id),
  predicate TEXT NOT NULL,
  object_entity_id INTEGER NOT NULL REFERENCES entities(id),
  valid_from TEXT,
  valid_to TEXT,
  source_refs_json TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'needs_review',
  confidence REAL
);
```

### Source perspectives

```sql
CREATE TABLE event_perspectives (
  id INTEGER PRIMARY KEY,
  event_id INTEGER NOT NULL REFERENCES events(id),
  article_id INTEGER NOT NULL REFERENCES articles(id),
  perspective_summary_en TEXT NOT NULL,
  perspective_summary_bn TEXT,
  distinctive_angle TEXT,
  key_additions_json TEXT NOT NULL DEFAULT '[]',
  disagreements_json TEXT NOT NULL DEFAULT '[]',
  source_refs_json TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'needs_review',
  UNIQUE(event_id, article_id)
);
```

This stores original Sarangsho comparison notes, not copied article text.

### Deep analysis

```sql
CREATE TABLE deep_analyses (
  id INTEGER PRIMARY KEY,
  event_id INTEGER REFERENCES events(id),
  article_id INTEGER REFERENCES articles(id),
  language TEXT NOT NULL,
  background TEXT,
  chronology_json TEXT NOT NULL DEFAULT '[]',
  verified_facts_json TEXT NOT NULL DEFAULT '[]',
  implications_json TEXT NOT NULL DEFAULT '[]',
  competing_explanations_json TEXT NOT NULL DEFAULT '[]',
  unresolved_questions_json TEXT NOT NULL DEFAULT '[]',
  source_refs_json TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'needs_review'
);
```

### Question metadata

Before adding columns, inspect the current `questions` definition. The intended additions are a stable `question_uid`, topic tags, validity/expiry metadata and a clear distinction between generated, manually authored and verified past questions.

## JSON record shapes

### Event

```json
{
  "event_uid": "EVT-BD-2026-000001",
  "title_en": "...",
  "title_bn": "...",
  "event_date": "2026-11-18",
  "status": "developing",
  "article_uids": ["ART-..."],
  "source_refs": [],
  "review_status": "approved"
}
```

### Entity and relationship

```json
{
  "entity_uid": "ORG-BD-000001",
  "entity_type": "institution",
  "name_en": "...",
  "name_bn": "...",
  "aliases": [],
  "source_refs": [],
  "review_status": "approved"
}
```

```json
{
  "relationship_uid": "REL-000001",
  "subject_uid": "ORG-BD-000001",
  "predicate": "member_of",
  "object_uid": "ORG-INT-000002",
  "valid_from": "2020-01-01",
  "valid_to": null,
  "source_refs": [],
  "review_status": "approved"
}
```

### Indicator

```json
{
  "indicator_uid": "BD-INFLATION-CPI",
  "country_code": "BGD",
  "name_en": "Consumer price inflation",
  "name_bn": "ভোক্তা মূল্যস্ফীতি",
  "unit": "percent",
  "frequency": "monthly",
  "definition": "...",
  "source": {
    "name": "...",
    "url": "https://..."
  },
  "observations": [
    {
      "period": "2026-10",
      "value": 0.0,
      "status": "preliminary",
      "published_at": "2026-11-..."
    }
  ]
}
```

Values above are illustrative shapes only, not factual observations.

## Provenance and approval

Every published factual record must include:
- Source reference(s).
- Retrieval/publication date where applicable.
- Review status.
- A distinction between verified fact, estimate, projection and editorial interpretation.

Valid review statuses should be explicit and consistent, for example `needs_review`, `approved`, `rejected` and `superseded`. Structural validation must never promote a record to `approved`.

## Compatibility rules

- New edition fields are optional until the minimum app version supports them.
- Unknown JSON fields must be safely ignored by older clients.
- Required fields cannot be removed or renamed without a schema-version change.
- Every package declares its schema version and minimum compatible app version.
- A package with broken references or unknown required schema version is rejected atomically.
