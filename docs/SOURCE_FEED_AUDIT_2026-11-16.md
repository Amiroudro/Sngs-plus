# First-pass publisher feed audit

**Audit date:** 2026-11-16  
**Scope:** Discovery and limited public-route inspection only. This is not an activation approval.  
**Important:** A web preview/parser error is not necessarily an HTTP failure. No source below is marked active from this audit alone.

## Evidence standard

A source is eligible for activation only after all of the following are confirmed from a publisher-controlled route:

1. Canonical publisher homepage and exact feed/sitemap URL.
2. Feed or sitemap returns structured article records, not an HTML error page.
3. At least one recent article has a credible publication timestamp and canonical article URL.
4. The route is compatible with the publisher's robots rules and terms.
5. Duplicate identity and update behaviour are tested.
6. A repeat fetch from the actual deployment environment succeeds.

Third-party RSS directories are useful for discovery, but they do not replace a direct check against the publisher's own endpoint. A feed endpoint that returns XML but cannot be parsed by a browser preview is not automatically broken.

## Direct route spot-checks

| Publisher | Candidate route checked | Observation | Audit status |
|---|---|---|---|
| Prothom Alo | https://www.prothomalo.com/feed/ | Preview rejected the XML content type; this is consistent with an RSS/XML response, but the items and recency were not inspected. | Unverified |
| The Daily Star | https://www.thedailystar.net/frontpage/rss.xml | Preview returned an ambiguous parser response ("400 OK"); no item-level confirmation. | Unverified |
| Jugantor | https://www.jugantor.com/feed/rss.xml | Preview returned an access-denied / page-not-found message; needs a direct deployment-side check and publisher route confirmation. | Unverified |
| Kaler Kantho | https://www.kalerkantho.com/rss.xml | Preview reported 403 Forbidden. Do not attempt to bypass the restriction. | Blocked in this preview; verify policy and route |
| Banglanews24 | https://www.banglanews24.com/rss/rss.xml | Feed content was readable, but the returned items were dated 25 May 2024. This is stale evidence, not proof of a currently maintained feed. | Stale observation |
| Jago News 24 | https://www.jagonews24.com/rss/rss.xml | Preview rejected the XML content type; item recency was not inspected. | Unverified |
| Bangla Tribune | https://www.banglatribune.com/feed | Preview returned 404 Not Found. Check for a publisher-documented replacement before retrying. | Route not found in this check |
| bdnews24.com | https://bdnews24.com/?widgetName=rssfeed&widgetId=1150&getXmlFeed=true | The preview rendered the HTML homepage rather than an RSS item list; the parameter order/route may be wrong or the endpoint may have changed. | Unverified |

## Discovery references

- Inkline's Bangladesh feed registry lists 43 publications and says its entries were feed-verified on 17 October 2026. Treat this as a discovery lead, not as Sarangsho Plus verification: https://inklinenews.com/feeds/bangladesh/
- The Bangladesh Department of Films and Publications' registered-newspaper list surfaced in this research is labelled through October 2022. It is useful for publisher identity and registration discovery, but too old to establish current activity or digital access: https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-dfp/2024/12/e9761b4826ce491f93965e851bf92d55.pdf
- A public directory updated 28 July 2026 separates national print newspapers, English newspapers and online-first publishers. It is a secondary directory and should be cross-checked against publisher-controlled sites: https://www.mediabangladesh.net/newspapers-bangladesh/

## Immediate implications

- Do not mark any of the eight spot-checked publishers active yet.
- Preserve blocked, stale and unavailable publishers in the source directory; these are source-health states, not reasons to erase a publisher.
- Avoid treating search-engine news feeds or third-party RSS registries as direct publisher integrations.
- Continue with official sitemap discovery and robots/terms review for the remaining candidates. Re-test all candidate routes from the actual deployment environment before activation.


## Publisher rights and reuse review

Technical accessibility is not permission to republish or create derivative study content. The publisher's own terms must be checked before enabling article-body collection, machine summarisation or display of excerpts.

| Publisher | Public policy evidence | Operational consequence |
|---|---|---|
| Prothom Alo | Its current Terms of Use explicitly permit access through RSS but also state that users may not make derivative works from its content; use is limited to personal, private and non-commercial purposes, and content sharing is subject to restrictions. | **Do not enable article-body summarisation or app redistribution without written permission or legal review.** RSS availability is not a blanket licence. |
| The Daily Star | The current site footer states that unauthorised use or reproduction of its content for commercial purposes is prohibited. | Treat article-body reuse and any public/commercial app distribution as permission-required; inspect full terms and obtain advice before enabling. |
| BSS | Its official site carries a 2026 copyright notice. The privacy page is not a content licence. | No republication or derivative-use permission established in this audit. Keep disabled for body processing until terms/licensing are confirmed. |

Prothom Alo policy: https://www.prothomalo.com/terms  
The Daily Star site: https://www.thedailystar.net/  
BSS official site: https://www.bssnews.net/  
BSS privacy policy: https://www.bssnews.net/privacy-policy

## Conflicting freshness evidence

Prothom Alo's /feed/ endpoint appears in multiple feed directories, but the evidence conflicts: Inkline's 17 October 2026 registry says its feed was verified, while Feeder's live listing reports the last post was three months ago. This is exactly why a feed should not be marked active based on a directory badge alone. Re-fetch the XML directly, inspect the newest item timestamps, compare them with the publisher's latest homepage articles, and repeat from the actual deployment environment.

- Inkline source entry: https://inklinenews.com/publications/prothom-alo/
- Feeder source entry: https://feeder.co/discover/aff49d20ea/prothom-alo-com

An independent public project, bangla-news-radar, reports that Jugantor, Kaler Kantho and bdnews24 return HTTP 403 to automated requests, and that The Daily Star's site-wide feed is stale while section feeds are current. This is useful corroboration for cautious handling, not a substitute for our own permitted deployment-side tests:
https://github.com/Claudefarid/bangla-news-radar

## Rights-aware activation rule

Add a separate rights state to the source registry. It must not be inferred from HTTP status or RSS presence:

- unknown: terms not reviewed
- rss_headlines_only: publisher terms allow feed discovery but do not establish rights for article bodies or derivative summaries
- permission_required: terms restrict the intended reuse or the permission scope is unclear
- licensed: written permission/licence is recorded, with scope and expiry
- disabled: source is not used for automated content processing

Until rights are established, use only publisher-permitted access patterns. Do not scrape around 403 responses, paywalls, bot blocks or other access controls. Keep source links and metadata for editorial discovery only where the publisher's terms permit that use. The app must not treat attribution or a link-back as a substitute for permission.
