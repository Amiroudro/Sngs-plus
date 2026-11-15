# Bangladesh newspaper source directory

**Purpose:** Candidate discovery list for Sarangsho Plus collection.  
**Status:** Candidate directory only. None of these 50 entries is automatically considered a verified live feed or an enabled collector route.

The list is grouped by publisher type and language, not ranked by circulation, accuracy or political orientation. Before activation, each source must be checked for current publication activity, canonical homepage, language, RSS/sitemap availability, robots.txt, publisher terms, timestamps, duplicate behaviour and technical reachability from the deployment environment.

## 25 Bangla national newspaper candidates

1. Prothom Alo
2. Bangladesh Pratidin
3. Kaler Kantho
4. Jugantor
5. Ittefaq
6. Samakal
7. Amader Shomoy
8. Janakantha
9. Manabzamin
10. Naya Diganta
11. Inqilab
12. Bonik Barta
13. Desh Rupantor
14. Ajker Patrika
15. Kalbela
16. Jaijaidin
17. Dainik Bangla
18. Sangbad
19. Sangram
20. Shomoyer Alo
21. Alokito Bangladesh
22. Amar Desh
23. Amar Sangbad
24. Dinkal Digital
25. Share Biz

## 11 English newspaper candidates

1. The Daily Star
2. Dhaka Tribune
3. New Age
4. The Financial Express
5. The Business Standard
6. The Business Post
7. Daily Sun
8. The Daily Observer
9. Bangladesh Post
10. The Bangladesh Today
11. The Asian Age

## 10 digital-first publisher candidates

1. bdnews24.com
2. Banglanews24
3. Jago News 24
4. Bangla Tribune
5. Dhaka Post
6. Risingbd
7. Barta24
8. Sarabangla
9. NewsBangla24
10. Daily Bangladesh

## 4 regional newspaper candidates

1. Dainik Azadi
2. Dainik Purbokone
3. Karatoa
4. Sonali Sangbad

## Additional news agencies

These are additional verification/discovery sources and are not included in the count of 50 newspapers:

- Bangladesh Sangbad Sangstha (BSS)
- United News of Bangladesh (UNB)

## Required verification record for every candidate

| Field | Meaning |
|---|---|
| publisher_name | Exact public publisher name |
| homepage_url | Canonical publisher homepage |
| language | Bangla, English or both |
| publisher_type | National, English, digital-first, regional or agency |
| feed_url | Official RSS/Atom URL, if available |
| sitemap_url | Official news sitemap, if available |
| section_routes | Public article section pages, if permitted |
| robots_status | Allowed, disallowed, unavailable or not checked |
| terms_status | Reviewed, unclear or not reviewed |
| rights_status | unknown, rss_headlines_only, permission_required, licensed or disabled |
| licence_scope | Permitted fields, processing, display, audience, territory and expiry, if licensed |
| permission_evidence | Public terms URL or written licence record |
| reachability | HTTP status and deployment-region result |
| latest_item_at | Latest verified publication timestamp |
| dedupe_identity | Canonical domain and URL normalisation rules |
| collection_status | Candidate, verified, active, stale, blocked or disabled |
| last_checked_at | Timestamp of the last verification |

A publisher may remain a valuable editorial source even when automated access is blocked. In that case, retain it in the directory and mark the access limitation; do not bypass the restriction or imply that it is being collected.

## Activation rule

A source becomes **active** only after its official public route and access conditions are checked and a test fetch returns identifiable article records with credible publication timestamps. A 200 response alone is insufficient: stale feeds, HTML error pages, incomplete sitemaps and aggregator results do not count as verified direct publisher coverage.

Aggregator discovery (for example, a search engine's news feed) must be recorded separately from direct publisher collection. It must never inflate the count of active direct publisher integrations.


## Rights-aware collection gate

A reachable RSS feed or public article page does not itself grant permission to store full article text, generate derivative summaries, or redistribute material in an app. Review each publisher's current terms and record a separate `rights_status`. If the intended processing or display is not clearly permitted, set `permission_required` or `disabled` and do not collect article bodies until permission is documented. Attribution and source links do not replace a licence. See `docs/SOURCE_FEED_AUDIT_2026-11-16.md` for the first policy checks and publisher-specific cautions.
