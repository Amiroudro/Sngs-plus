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


## 50-publisher domain coverage update (16 Nov 2026)

The candidate directory now has domain leads for all 50 candidates. Sonali Sangbad's publisher homepage is confirmed at sonalisangbad.com, but its current feed endpoint and freshness remain unverified. Domain leads are not equivalent to feed verification or permission to reuse content.

| Group | Candidate | Domain lead | Evidence class |
|---|---|---|---|
| Bangla national | Prothom Alo | prothomalo.com; en.prothomalo.com | Existing collector routes |
| Bangla national | Bangladesh Pratidin | bd-pratidin.com | GDI / directory lead |
| Bangla national | Kaler Kantho | kalerkantho.com | GDI / directory lead |
| Bangla national | Jugantor | jugantor.com | Existing collector route |
| Bangla national | Ittefaq | ittefaq.com.bd | GDI / directory lead |
| Bangla national | Samakal | samakal.com | GDI / directory lead |
| Bangla national | Amader Shomoy | amadershomoys.com | Third-party directory lead |
| Bangla national | Janakantha | dailyjanakantha.com | GDI / directory lead |
| Bangla national | Manabzamin | mzamin.com | Third-party directory lead |
| Bangla national | Naya Diganta | dailynayadiganta.com | GDI / directory lead |
| Bangla national | Inqilab | dailyinqilab.com | Research / directory lead |
| Bangla national | Bonik Barta | bonikbarta.net | GDI / directory lead |
| Bangla national | Desh Rupantor | deshrupantor.com | GDI / directory lead |
| Bangla national | Ajker Patrika | ajkerpatrika.com | GDI / directory lead |
| Bangla national | Kalbela | kalbela.com | Third-party directory lead |
| Bangla national | Jaijaidin | jaijaidinbd.com | Research / directory lead |
| Bangla national | Dainik Bangla | dainikbangla.com.bd | Publisher About Us page |
| Bangla national | Sangbad | sangbad.net; sangbad.net.bd | Publisher Terms page / Inkline directory lead |
| Bangla national | Sangram | dailysangram.com | Third-party directory lead |
| Bangla national | Shomoyer Alo | shomoyeralo.com | Publisher homepage |
| Bangla national | Alokito Bangladesh | alokitobangladesh.com | Publisher homepage |
| Bangla national | Amar Desh | amardeshonline.com | Third-party directory lead |
| Bangla national | Amar Sangbad | amarsangbad.com | Third-party directory lead |
| Bangla national | Dinkal Digital | dainikdinkal.net | News-agency federation directory lead |
| Bangla national | Share Biz | sharebiz.net | Third-party report lead |
| English | The Daily Star | thedailystar.net | Existing collector route |
| English | Dhaka Tribune | dhakatribune.com | Existing collector route / GDI |
| English | New Age | newagebd.net | Existing source map / GDI |
| English | The Financial Express | thefinancialexpress.com.bd | Existing collector route |
| English | The Business Standard | tbsnews.net | Existing collector route / GDI |
| English | The Business Post | businesspostbd.com | MRDI / directory lead |
| English | Daily Sun | daily-sun.com | Existing source map / directory lead |
| English | The Daily Observer | observerbd.com | Existing source map / directory lead |
| English | Bangladesh Post | bangladeshpost.net | Government media contact list |
| English | The Bangladesh Today | thebangladeshtoday.com | Government media contact list |
| English | The Asian Age | dailyasianage.com | Government media contact list |
| Digital-first | bdnews24.com | bdnews24.com | GDI / publisher site |
| Digital-first | Banglanews24 | banglanews24.com | GDI / directory lead |
| Digital-first | Jago News 24 | jagonews24.com | GDI / directory lead |
| Digital-first | Bangla Tribune | banglatribune.com | GDI / directory lead |
| Digital-first | Dhaka Post | dhakapost.com | GDI / directory lead |
| Digital-first | Risingbd | risingbd.com | GDI / directory lead |
| Digital-first | Barta24 | barta24.com | Inkline / directory lead |
| Digital-first | Sarabangla | sarabangla.net | GDI / directory lead |
| Digital-first | NewsBangla24 | newsbangla24.com | GDI / directory lead |
| Digital-first | Daily Bangladesh | daily-bangladesh.com | Third-party directory lead |
| Regional | Dainik Azadi | dainikazadi.net (alternate directory lead: dainikazadi.com) | Inkline feed-registry listing / regional directory lead |
| Regional | Dainik Purbokone | dainikpurbokone.net | GDI / regional directory lead |
| Regional | Karatoa | karatoa.com.bd | Regional newspaper directory lead |
| Regional | Sonali Sangbad | sonalisangbad.com | Publisher homepage and e-paper route; feed freshness unverified |



### Sonali Sangbad domain follow-up

The publisher-controlled homepage is reachable at [sonalisangbad.com](https://sonalisangbad.com/), with a current homepage article dated 14 November 2026. Its [e-paper route](https://sonalisangbad.com/epaper/) shows an edition dated 11 November 2026. A third-party directory also identifies sonalisangbad.com as the official site. This confirms an active publisher homepage and recent e-paper, but no RSS/news-sitemap route has been verified. The source remains source_enabled=false, metadata pending, automated processing pending and body processing not permitted.

### Domain and permission registry

The machine-readable registry now contains 55 host records: all 50 candidate publisher identities have a domain lead, Prothom Alo has separate Bangla and English hosts, and BSS/UNB are additional agencies. All records remain pending for metadata and page-metadata use; automated processing is pending or restricted for flagged sources, and article bodies are not permitted. The registry's default for an unlisted or malformed publisher URL is deny.

The third-party directories above are discovery aids. The canonical domain for each candidate still needs confirmation against a publisher-controlled site. The route audit must then verify feed structure, recency, robots rules and the intended use permitted by current terms. No source should be marked active based on a directory listing alone.

Every registry source_enabled flag currently remains false. The collector requires the database source to be explicitly enabled as well as rights-approved. Migration 003 adds separate metadata, automated-processing, page and body gates; the manual dry-run-first sync tool copies reviewed DB decisions into the Engine registry and refuses conflicting source records.


## Third-party RSS registry cross-check

Inkline's 17 October 2026 Bangladesh registry lists 43 publications and says each listed feed was machine-verified in that pass. It includes 32 publisher identities that overlap the current candidate inventory or the two additional agencies. The machine registry records these as third-party feed leads only; it does not store an assumed feed URL and does not change any rights status.

Examples with individual Inkline publication pages surfaced in this audit include [Bangladesh Pratidin](https://inklinenews.com/publications/bangladesh-pratidin/), [Daily Janakantha](https://inklinenews.com/publications/daily-janakantha/), [Samakal](https://inklinenews.com/publications/samakal/), [Bonik Barta](https://inklinenews.com/publications/bonik-barta/), [Manab Zamin](https://inklinenews.com/publications/manab-zamin/), [Daily Naya Diganta](https://inklinenews.com/publications/daily-naya-diganta/), [Daily Sun](https://inklinenews.com/publications/daily-sun/), [The Business Post](https://inklinenews.com/publications/the-business-post/), [Risingbd](https://inklinenews.com/publications/risingbd/), [Daily Inqilab](https://inklinenews.com/publications/daily-inqilab/), [New Age](https://inklinenews.com/publications/new-age/), [Bangla Tribune](https://inklinenews.com/publications/bangla-tribune/), [Dhaka Tribune](https://inklinenews.com/publications/dhaka-tribune/), [The Business Standard](https://inklinenews.com/publications/the-business-standard/), [The Daily Star](https://inklinenews.com/publications/the-daily-star/), [Dainik Azadi](https://inklinenews.com/publications/dainik-azadi/) and [BSS](https://inklinenews.com/publications/bangladesh-sangbad-sangstha/). These pages are useful for feed discovery and coverage metadata, not permission to reuse articles.

Inkline's profile pages report that Daily Inqilab and Risingbd robots.txt disallow several named AI crawlers in a scan dated 16 August 2026. This is a third-party report that must be checked against each publisher's current robots.txt and terms before any automated processing. The rights registry sets automated_processing_status=restricted for both sources until their current publisher-controlled robots.txt and terms are rechecked; the collector must not work around those rules.

The registry's third-party feed claim is deliberately distinct from direct verification by Sarangsho Plus. Exact feed URL, direct response, item freshness, parsing, robots compatibility and permitted use remain unverified until tested from the actual deployment environment.


## Automated processing permission is a separate gate

Sarangsho Plus uses automated classification, fact extraction, translation, question generation and summarisation. Permission to read a public feed or collect a headline does not, by itself, establish permission for these processing steps. The operational registry therefore requires a separate automated_processing_status=approved record with a defined automated_processing_scope, evidence and a current review date before metadata enters the Engine. Article-page extraction and article-body processing retain their additional, separate gates.

Daily Inqilab and Risingbd have a third-party reported AI-crawler robots warning in Inkline's 16 August 2026 scan. This is recorded as a review warning, not as a final legal conclusion. Their current publisher-controlled robots.txt and terms must be checked directly before any automated processing is considered. The custom collector User-Agent must never be used to work around a restriction aimed at AI crawlers.


## Follow-up domain resolution: Sonali Sangbad (16 Nov 2026)

The previously unresolved regional candidate now has a credible canonical-domain lead: **https://sonalisangbad.com/**. The publisher-controlled homepage is indexed with current headlines, and its e-paper page shows an edition dated 11 November 2026. This is sufficient to resolve the domain-lead gap, but not to verify a feed, robots compatibility, automated-processing permission or article-body rights.

- Publisher homepage: https://sonalisangbad.com/
- Publisher e-paper: https://sonalisangbad.com/epaper/
- Current indexed e-paper date observed: 11 November 2026.
- Independent corroboration: the Media Resources Development Initiative lists Sonali Sangbad among online media; a 2026 newspaper directory identifies sonalisangbad.com as its official site.
- Audit disposition: `domain_lead_found`; feed route, robots, terms and rights remain unverified/pending. Do not activate.

References:
- Publisher homepage: https://sonalisangbad.com/
- Publisher e-paper: https://sonalisangbad.com/epaper/
- MRDI media list: https://mrdibd.org/paonlmedia/
- KhoborBox directory (27 Sep 2026): https://khoborbox.com/bangladesh-newspaper-directory/

## Additional feed discovery leads (not direct verification)

A fresh third-party discovery pass found a public list of eight Bangladesh RSS candidates: The Daily Star, bdnews24.com, Banglanews24, Jugantor, Jago News 24, Kaler Kantho and Prothom Alo, plus BD24Live. These exact routes are leads only; they do not override our earlier direct-route observations (including stale Banglanews24 output and preview access errors for some feeds). Inkline's 43-source registry remains a useful independent discovery catalogue but is not publisher permission and does not establish freshness at our deployment.

- Chetmail feed directory: https://www.chetmail.com/feeds/local-news/bangladesh
- Inkline Bangladesh registry: https://inklinenews.com/feeds/bangladesh/
- FeedSpot directory: https://rss.feedspot.com/bangladesh_news_rss_feeds/

**Audit decision:** domain coverage is now 50/50 at the candidate-lead level. Direct publisher feed verification and rights clearance remain a separate, incomplete workstream. No status in the operational rights registry is changed by this research.

The machine-readable route matrix is [engine-v2/state/source_routes.json](../engine-v2/state/source_routes.json). It records 55 hosts, eight feed-route leads, zero directly verified routes and zero enabled sources. Its CI test checks exact host parity with source_rights.json and confirms that source-enabled, body-rights and automated-processing states agree.


## Sonali Sangbad route recheck (16 Nov 2026)

A fresh publisher-site check confirms the homepage is actively publishing: the homepage search index currently surfaces multiple November 2026 headlines, and an individual article is dated 13 November 2026. The e-paper route also reports a 11 November 2026 edition. This upgrades the evidence from a domain lead to **publisher-site activity observed**, but does not establish a reliable feed integration or any reuse permission.

- Homepage: https://sonalisangbad.com/
- Example current article: https://sonalisangbad.com/2026/11/13/শাহ-মখদুম-দরগাহ-শরিফের-নব/
- E-paper: https://sonalisangbad.com/epaper/
- Feed route probe: `https://sonalisangbad.com/feed` returned an RSS content type to the research fetcher, but the fetcher could not parse/display the RSS payload. Treat as a **feed-route lead**, not a verified feed: item structure, timestamps, freshness and direct collector parsing still need testing in the deployment environment.
- `https://sonalisangbad.com/rss.xml` was not accessible to the research fetcher.
- `https://sonalisangbad.com/robots.txt` was not accessible to the research fetcher. This is unknown/unverified, not evidence that crawling is allowed or disallowed.
- Terms of use / automated processing permission: not located in this pass; remains pending.
- Rights registry remains unchanged: metadata pending, page metadata pending, automated processing pending, body not permitted, source disabled.

Independent directories corroborate the publisher identity and Rajshahi regional classification, but are not permission evidence. The MRDI media list includes Sonali Sangbad; KhoborBox lists its homepage and e-paper; Inkline's 43-feed registry does not list it in the 17 October 2026 pass.

**Disposition:** `publisher_site_active_feed_lead_unverified_rights_pending`. Do not enable.


## Concrete RSS route leads from third-party directories (16 Nov 2026)

Chetmail's Bangladesh directory and the public Plenary OPML export independently expose the following candidate routes. These are **discovery leads**, not direct fetch tests by Sarangsho Plus. No route is promoted to `verified` or `active` from this table.

| Publisher | Candidate feed URL | Audit status |
|---|---|---|
| The Daily Star | `https://www.thedailystar.net/frontpage/rss.xml` | Third-party route lead; section-feed freshness must be checked |
| BD24Live | `https://www.bd24live.com/feed` | Third-party route lead; not in the 50-candidate core |
| bdnews24.com | `https://bdnews24.com/?widgetName=rssfeed&widgetId=1150&getXmlFeed=true` | Third-party route lead; automated access has been reported as blocked by an independent project |
| Banglanews24 | `https://www.banglanews24.com/rss/rss.xml` | Third-party route lead; freshness and parser output unverified |
| Jugantor | `https://www.jugantor.com/feed/rss.xml` | Third-party route lead; automated access has been reported as blocked by an independent project |
| Jago News 24 | `https://www.jagonews24.com/rss/rss.xml` | Third-party route lead; freshness and parser output unverified |
| Kaler Kantho | `https://www.kalerkantho.com/rss.xml` | Third-party route lead; automated access has been reported as blocked by an independent project |
| Prothom Alo | `https://www.prothomalo.com/feed/` | Third-party route lead; a feed aggregator previously reported stale output, so freshness is unresolved |

Sources:
- Chetmail Bangladesh RSS directory: https://www.chetmail.com/feeds/local-news/bangladesh
- Plenary Bangladesh OPML: https://github.com/plenaryapp/awesome-rss-feeds/blob/master/countries/with_category/Bangladesh.opml
- Independent implementation notes and access observations: https://github.com/Claudefarid/bangla-news-radar

**Next verification required for each route:** fetch from the intended deployment region using the documented collector identity; record HTTP status and content type; parse at least five items; verify non-empty title, canonical URL and timezone-aware publication date; calculate newest-item age; check robots and publisher terms separately; then test duplicate identity against an overlapping source. A 403 or failed fetch is recorded as inaccessible from that environment, not proof the publisher has shut down. Never rotate identities or evade blocks to force a successful fetch.


## Collector route inventory reconciliation (16 Nov 2026)

A comparison of the imported `step1_collect.py` constants with the original source notes found that the collector contains 19 publisher-route entries (RSS, sitemap, section-page and historical blocked/stale routes), while the first route ledger only represented eight third-party directory leads. The two sets are now kept separately in `engine-v2/state/source_routes.json`:

- `sources`: 55 publisher hosts and eight third-party route leads. These remain discovery-only.
- `collector_route_inventory`: 19 routes configured or historically tested by the imported Engine.
- Each collector route records its observation date (15 Nov 2026), evidence environment (`original_engine_development_vm`), and explicit false values for deployment verification, rights approval and source activation.

The top of `step1_collect.py` now labels its route notes as historical original-VM observations, not current deployment verification. This fixes the misleading phrase “verified live from this VM” and removes a reference to a route report that is not present in this imported repository. Historical 403/404/stale observations remain visible; they are not bypassed or silently reclassified.

**Current status after reconciliation:** 55 publisher hosts; 8 third-party route leads; 19 historical/configured collector routes; 0 deployment-verified routes; 0 enabled publishers; 0 article-body permissions. This is a better inventory, not an activation event.


## Official terms and copyright-page review (16 Nov 2026)

This is a first-pass reading of publisher-controlled pages, not a legal opinion and not a licence. It records restrictions or uncertainty so that RSS discovery is never mistaken for permission to process or republish.

| Publisher | Official page reviewed | What the page says / what remains unclear | Disposition |
|---|---|---|---|
| Prothom Alo (Bangla and English) | https://www.prothomalo.com/terms and https://en.prothomalo.com/terms | Reserves its IP, prohibits derivative works and prohibits sharing modified content. RSS is listed as an access channel, not as a grant to create summaries or republish. | Keep disabled; written permission/legal review required for planned derivative summaries. |
| The Financial Express | https://thefinancialexpress.com.bd/terms | Copyright notice says site material is protected, use is personal/non-commercial, and reproduction requires prior written approval. | Keep disabled; seek written approval for the intended use. |
| UNB | https://unb.com.bd/privacy-policy/ | Its policy says website news, photos, graphics and videos are UNB property and unauthorised use, reproduction, distribution, display or transmission is prohibited. | Keep disabled; obtain explicit permission. |
| Jugantor | https://www.jugantor.com/terms | Official terms page found. The reviewed text covers access, third-party links, termination and Bangladesh governing law; it does not expressly grant automated collection, summarisation or republication rights. | Keep disabled; rights scope unresolved. |
| Banglanews24 | https://www.banglanews24.com/policy | Official policy describes content as for personal information only, says it is not for commercial use, and describes reader access as reading-only. | Keep disabled; no automated reuse permission identified. |
| The Daily Star | https://www.thedailystar.net/privacypolicy | Official privacy policy says it forms part of the Terms of Use, but the full terms page was not retrievable in this review. | Keep disabled; full terms and permission scope unresolved. |
| Dhaka Tribune | https://www.dhakatribune.com/footer | Official footer advertises a Terms of Use link, but the destination text was not retrievable in this review. | Keep disabled; full terms and permission scope unresolved. |
| The Business Standard | https://epaper.tbsnews.net/terms-conditions | The located terms concern e-paper subscription billing/cancellation, not general article-content reuse or automated processing. | Keep disabled; general content terms and permission scope unresolved. |

**Important distinction:** the BSS copyright footer and any publisher copyright notice are ownership/attribution evidence, not permission to collect or generate derivative study material. No rights-registry permission fields were changed by this review. All sources remain disabled and article-body processing remains prohibited.


## Additional official terms review: Bangladesh Pratidin and Bangla Tribune (16 Nov 2026)

This review records publisher-controlled terms, not a legal opinion or permission grant.

| Publisher | Official terms page | Findings | Disposition |
|---|---|---|---|
| Bangladesh Pratidin | https://www.bd-pratidin.com/page/terms | The site grants personal viewing/downloading/printing only, prohibits republication, commercial use, editing/modification and unauthorised redistribution, and expressly prohibits automated data collection (including scraping, data mining and harvesting) without permission. | Keep disabled. Obtain express written permission covering automated collection and the intended downstream processing/display. |
| Bangla Tribune | https://www.banglatribune.com/terms | The terms prohibit systematic or automated data collection without express written consent, and prohibit republication, commercial exploitation, modification and redistribution except where content is expressly made available for redistribution (then limited to within the organisation). | Keep disabled. Obtain express written consent and confirm that it covers automated processing, study summaries and public app display. |

The terms do not establish that headline-only metadata collection is permitted. Do not infer a narrower permission from the fact that a page or feed is publicly reachable. No rights-registry permission fields were changed.

References:
- Bangladesh Pratidin official terms: https://www.bd-pratidin.com/page/terms
- Bangla Tribune official terms: https://www.banglatribune.com/terms


## Additional official terms review: Ajker Patrika (16 Nov 2026)

The publisher-controlled [Ajker Patrika terms page](https://www.ajkerpatrika.com/user-terms-and-conditions) says its intellectual property is not licensed for commercial use, discourages copying and creating new works from its content, and prohibits sharing content with other organisations or digital platforms in either original or modified form. The page does not provide an affirmative licence for automated collection, derivative exam summaries or public app redistribution.

**Disposition:** keep Ajker Patrika disabled. Obtain written permission for the precise collection, automated-processing and display workflow before considering activation. This is a terms review, not a legal opinion or permission grant.

Daily Ittefaq's located [Privacy Policy](https://www.ittefaq.com.bd/privacy-policy/) concerns personal-data handling and is not a general article-content licence. Its general content terms remain unreviewed; do not treat the privacy policy as permission or as a content restriction finding.


## Additional official terms review: Daily Ittefaq and Samakal (16 Nov 2026)

| Publisher | Official page | Finding | Disposition |
|---|---|---|---|
| Daily Ittefaq | https://www.ittefaq.com.bd/terms | Terms state that its content and related IP belong to Ittefaq/licensors; users receive read-only, personal/private/non-commercial access; users may not make derivative works or share modified/altered content on other digital platforms. No licence for automated collection, derivative study notes or app redistribution is granted. | Keep disabled. Written permission is required for the proposed workflow. |
| Samakal | https://onlinebn.samakal24.com/terms | The located page contains general disclaimers, comment rules and communications provisions. The reviewed text does not clearly grant or expressly address automated collection, summarisation or app redistribution. | Review inconclusive. Keep disabled; seek written clarification/permission before processing. |

A third-party feed directory lists Samakal and Ittefaq as feed-verified in its 17 October 2026 registry pass. This is only a third-party directory claim, not direct verification from our deployment environment and not a content-use licence.

No source permissions were activated by this review.
