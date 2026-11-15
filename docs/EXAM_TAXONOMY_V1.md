# Sarangsho Plus exam-topic taxonomy v1

**Status:** App-facing taxonomy specification. The Engine v2 primary topic IDs remain unchanged until a separately tested classifier upgrade is implemented.

## Design rule

Keep three concepts separate:

1. **Engine topic:** the current deterministic Step 3 primary topic. It is a triage/classification input, not the final study taxonomy.
2. **Study topic tags:** one or more reader-facing syllabus tags attached to the story. These support search, filters and cross-topic stories.
3. **Exam tracks:** the examinations for which the item is useful (BCS, Bangladesh Bank/bank recruitment, government recruitment, or general knowledge).

A story may have multiple study tags. Do not force agriculture, health or education stories into a single broad “Bangladesh” or “Science” bucket.

## Reader-facing study topic tags

| Tag ID | Reader label | Typical coverage |
|---|---|---|
| BD-GOVERNANCE | Constitution, government and administration | Constitution, parliament, cabinet, ministries, public administration, local government, elections, public institutions |
| BD-LAW-JUSTICE | Law, courts and justice | Legislation, judgments, courts, legal reform, criminal justice, policing policy |
| BD-HUMAN-RIGHTS | Human rights and civic rights | Fundamental rights, labour rights, child rights, gender rights, civil liberties, access to justice |
| BD-ECONOMY | Economy and public finance | GDP, inflation, budget, revenue, debt, poverty, trade, employment, exports and imports |
| BD-BANKING | Banking and financial systems | Bangladesh Bank, monetary policy, banks, NPLs, financial inclusion, payments, capital markets |
| BD-AGRICULTURE | Agriculture, food and fisheries | Crops, food security, fisheries, livestock, agricultural research, farm policy |
| BD-EDUCATION | Education and skills | Education policy, curriculum, exams, universities, literacy, skills and research institutions |
| BD-HEALTH | Public health and healthcare | Disease surveillance, health systems, vaccination, hospitals, medicine policy, nutrition |
| BD-ENVIRONMENT | Environment and climate | Climate change, biodiversity, pollution, forests, rivers, coastal risk, climate finance |
| BD-DISASTER | Disaster risk and response | Cyclones, floods, earthquakes, warnings, relief, recovery and resilience |
| BD-INFRASTRUCTURE | Infrastructure and development | Transport, ports, power grids, water, housing, major public projects and urban development |
| BD-ENERGY | Energy and natural resources | Electricity, fuel, gas, renewables, mining, energy security and transition |
| BD-SCI-ICT | Science, technology and ICT | AI, cybersecurity, space, telecom, digital governance, scientific discoveries and innovation |
| BD-SOCIETY | Society, culture and social development | Demography, social protection, NGOs, gender equality, culture, heritage and social welfare |
| INT-ORGANISATIONS | International organisations | UN, IMF, World Bank, ADB, WTO, regional organisations and multilateral agreements |
| INT-RELATIONS | International affairs and diplomacy | Bilateral relations, foreign policy, conflict, sanctions, treaties, border and water diplomacy |
| SPORT-CURRENT | Sports and major competitions | Major tournaments, records, medals, international sporting institutions |
| PEOPLE-AWARDS | People, awards and observances | Major appointments, notable deaths, national/international awards and important observance themes |

## Mapping from current Engine v2 topics

This is a multi-label mapping, not a one-to-one replacement. The existing IDs in RULES.md remain canonical for the current engine.

| Current Engine topic | Candidate study tags |
|---|---|
| BD-GOV | BD-GOVERNANCE, BD-LAW-JUSTICE, BD-HUMAN-RIGHTS |
| BD-ECO | BD-ECONOMY, BD-AGRICULTURE, BD-INFRASTRUCTURE, BD-ENERGY |
| BD-BANK | BD-BANKING, BD-ECONOMY, BD-SCI-ICT |
| BD-NATL | BD-SOCIETY, BD-HUMAN-RIGHTS, BD-EDUCATION |
| INT-ORG | INT-ORGANISATIONS, BD-ECONOMY, BD-HEALTH, BD-ENVIRONMENT |
| INT-REL | INT-RELATIONS |
| ENV | BD-ENVIRONMENT, BD-DISASTER, BD-AGRICULTURE |
| SCI | BD-SCI-ICT, BD-HEALTH, BD-EDUCATION, BD-ENERGY |
| SPORT | SPORT-CURRENT |
| PEOPLE | PEOPLE-AWARDS, BD-SOCIETY |

The mapping only proposes candidate tags. A tag is assigned only when the article's headline/body evidence supports it. Do not attach every candidate tag automatically.

## Exam-track relevance

Use separate exam_tracks values:

- bcs_preliminary
- bcs_written
- bangladesh_bank
- bank_recruitment
- government_recruitment
- general_knowledge

A tag is not itself an exam score. Record a 0–10 score, a short evidence-based reason and the relevant tracks separately. The scoring contract in docs/EDITORIAL_SCORING_CONTRACT.md remains authoritative.

## Quality and retention

- Keep the full source metadata archive regardless of study score, subject to publisher terms and access restrictions.
- Scores 8–10: full bilingual study note, verified facts, background, vocabulary and exam practice.
- Scores 5–7: concise bilingual note, essential facts and a smaller practice set.
- Scores 2–4: short factual note and source link.
- Scores 0–1: archive/search record only.
- Disputed claims, sensitive allegations and public-safety alerts always carry a human-review flag.
- Translation quality must be tracked independently. Deterministic word substitution is not a fluent translation; generated Bangla content remains needs_review until checked.
- Do not generate exam questions from unverified or disputed facts.

## Implementation sequence

1. Store topic_tags_json, exam_tracks_json, taxonomy version and independent exam score in article_exam_assessments.
2. Build a rule-based candidate-tag pass from article evidence, with explicit precision tests and a “no tag” outcome.
3. Add tests for ambiguous cross-topic stories (e.g. cyclone damage to agriculture, IMF climate finance, public-health emergency).
4. Expose filters in the app only after tag assignments are validated.
5. Add LLM-assisted translation only with source-grounded prompts, no invented detail, quality status and human approval before publication.
