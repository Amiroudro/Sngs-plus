# Reconciliation note — ui-ux-pro-max deals vs NEXUS (Stage 1, 2026-11-18)

Rule applied (from the task): if the skill's dealt palette, pairing or
style conflicts materially with the NEXUS spec in
`~/workspace/sarangsho-plus/REDESIGN_PLAN.md` §2, **NEXUS wins** — the
skill's result is used only to refine/validate it. Nothing from the skill
was silently dropped; every conflict below names the deal, the NEXUS
value, and the choice.

Reference: `MASTER.md` §0 summarises this; this file is the full record.

## Exact search commands run

All run from `~` (skill tool invoked by full path, as required):

1. `python3 ~/workspace/custom-skills/ui-ux-pro-max/scripts/search.py "education news learning app" --design-system -p "Sarangsho Plus"`
2. `python3 ~/workspace/custom-skills/ui-ux-pro-max/scripts/search.py "Bengali editorial newspaper mobile app" --design-system -p "Sarangsho Plus"`
3. `python3 ~/workspace/custom-skills/ui-ux-pro-max/scripts/search.py "news reading editorial minimal" --design-system -p "Sarangsho Plus"`
4. `python3 ~/workspace/custom-skills/ui-ux-pro-max/scripts/search.py "material design mobile app" --stack flutter`
5. `python3 ~/workspace/custom-skills/ui-ux-pro-max/scripts/search.py "mobile exam preparation learning" --design-system -p "Sarangsho Plus"`
6. Persist (query 3, the closest deal): `python3 ~/workspace/custom-skills/ui-ux-pro-max/scripts/search.py "news reading editorial minimal" --design-system --persist --tokens dtcg -p "Sarangsho Plus" --output-dir ~/workspace/sarangsho-plus`

Also read: `~/workspace/custom-skills/ui-ux-pro-max/references/pro-rules.md`
(pre-delivery checklist thinking applied in `MASTER.md` §14; no code is
delivered in this stage, so the checklist is recorded as the gate for
later stages, not claimed as done).

**0-result searches: none.** All five queries returned results. No
retry was needed. No `--force` was used (no `MASTER.md` existed before
the persist run; verified with `ls` first).

## Per-search results

### 1. "education news learning app" — Claymorphism / Feature-Rich Showcase
- Palette: indigo `#4F46E5` + orange `#EA580C` on `#EEF2FF`.
- Pairing: Baloo 2 / Comic Neue (kids, playful).
- Style: soft 3D, chunky, bubbly, thick borders, double shadows, rounded 16–24px.
- **Verdict: rejected in full.** Indigo + orange is the opposite of the
  approved cool-crimson-on-white system; the playful kids fonts are wrong
  for an exam app; chunky rounded cards with double shadows are exactly
  the card-heavy dashboard the redesign removes. The deal's own
  "AVOID: Dark modes" also conflicts — the app ships a full dark theme.
- Kept: nothing except the generic checklist items (contrast 4.5:1,
  reduced motion, visible focus).

### 2. "Bengali editorial newspaper mobile app" — Minimalism & Swiss Style / Hero + Features + CTA
- Palette: editorial black `#18181B` + pink accent `#EC4899` on `#FAFAFA`.
- Pairing: Outfit / Work Sans (geometric, modern, clean).
- Style: clean, spacious, functional, white space, high contrast,
  geometric, grid-based.
- **Verdict: style agreed, palette/pairing differed.**
  - Agreed: the Swiss/minimalist style *is* the NEXUS spirit
    (geometric, high contrast, grid, white space, type-led hierarchy).
    This validates the direction.
  - Differed: pink `#EC4899` accent → NEXUS crimson `#B4232A` chosen;
    `#FAFAFA` background → true white `#FFFFFF` chosen; Outfit/Work Sans
    → system Bengali/Latin fonts (no font files may be bundled).
  - The "Hero + Features + CTA" landing pattern does not apply to an
    app's Home (masthead + numbered list instead) — pattern not used.

### 3. "news reading editorial minimal" — Minimalism & Swiss Style / Hero-Centric Design (PERSISTED)
- Palette: breaking red `#DC2626` + link blue `#1E40AF` on `#FEF2F2`,
  foreground `#450A0A`.
- Pairing: Newsreader / Roboto (news, editorial, trustworthy, readable).
- Style: Minimalism & Swiss (same as query 2). Effects: subtle hover,
  sharp shadows if any, clear type hierarchy.
- **Verdict: closest deal — style and editorial mood agreed; palette and
  fonts differed and were overridden in MASTER.md/tokens.json.**
  - Agreed: Swiss style; editorial typography mood; "clear type
    hierarchy"; red as the primary colour family.
  - Differed: `#DC2626` is warmer/brighter than the approved cool
    crimson `#B4232A` (hue ≈ 357°, no orange) → `#B4232A` chosen
    (dark `#E5484D`); blue accent `#1E40AF` → rejected (one accent only,
    no blue); pink-tinted background `#FEF2F2` → true white `#FFFFFF`;
    foreground `#450A0A` (dark red-brown) → near-black ink `#111110`;
    Newsreader/Roboto → system fonts (offline app, APK size budget).
    Generic card radius 12px + shadow scale → NEXUS split (news 0px,
    no shadows; learning 12px, one soft shadow).
  - The "Hero-Centric" landing pattern (full-bleed hero + CTA) was not
    used — the app's hero is the asymmetric `TopStoryHero` (red numeral
    block + paper, §7.2 of MASTER.md).
  - This deal was the persist source only because it was the closest;
    its conflicting values were then replaced in both files (the
    persisted `#DC2626`/`#1E40AF`/`Newsreader` values now appear in
    MASTER.md/tokens.json only inside reconciliation notes, never as
    adopted tokens — verified by grep).

### 4. "material design mobile app" — Flutter stack (3 results)
- Use `ColorScheme` (Material 3 colour system); use `ThemeData`
  (consistent theming, no hardcoded colours); use integration tests.
- **Verdict: agreed, with one refinement.** Token-driven theming via
  `ThemeData`/`ColorScheme` matches the plan (all tokens in
  `app/lib/widgets/app_theme.dart`). The skill's `ColorScheme.fromSeed()`
  example is NOT used — NEXUS tokens are explicit fixed hex values, not
  seed-derived. Integration-test guidance is noted for later stages
  (Stage 1 delivers documents only; `flutter test` gates live in
  REDESIGN_PLAN §5).

### 5. "mobile exam preparation learning" — Flat Design / Feature-Rich Showcase
- Palette: education teal `#0D9488` + amber `#D97706` on `#F0FDFA`.
- Pairing: Baloo 2 / Comic Neue (again — playful kids).
- Style: 2D, minimalist, bold colours, no shadows, clean lines,
  typography-focused.
- **Verdict: effect agreed, palette/pattern/pairing rejected.**
  - Agreed: "no gradients/shadows, clean lines, typography-focused" —
    matches NEXUS.
  - Differed: teal + amber → crimson `#B4232A` chosen (no teal/amber
    brand colours; amber survives only as `warning` state colour);
    Baloo 2/Comic Neue → system fonts; "Feature-Rich Showcase" (feature
    grid/cards, CTA repetition) → rejected, Home is a numbered list.

## What the skill contributed (kept)

- Style validation: Minimalism & Swiss Style in 2 of 4 design-system
  deals independently confirms the NEXUS direction.
- Effect rule "no gradients/shadows, clean lines, typography-focused".
- Editorial typography *mood* (trustworthy, readable) as the intent to
  approximate with system-font weight/size.
- Generic UX rules kept wholesale (skill priority table + pro-rules.md):
  ≥44px touch targets (48dp Android), body ≥12px (Bengali body ≥14px),
  4.5:1 contrast, no emoji as icons, Material vector icons only,
  consistent icon sizing, 8dp spacing rhythm, visible focus/disabled
  states, reduced-motion + 200% text support, safe-area compliance,
  token-driven theming, shared motion tokens, pre-delivery checklist
  structure (adapted to this app in MASTER.md §14).
- Flutter stack guidance: `ThemeData`/`ColorScheme`, no hardcoded colours.

## What NEXUS overruled (summary table)

| Aspect | Skill dealt | NEXUS (chosen) |
|---|---|---|
| Accent | Indigo `#4F46E5`, pink `#EC4899`, teal `#0D9488`, `#DC2626` + blue `#1E40AF` | Cool crimson `#B4232A` / dark `#E5484D`, one accent only |
| Background | `#EEF2FF`, `#FAFAFA`, `#FEF2F2`, `#F0FDFA` (tinted) | True white `#FFFFFF` (light) / `#131311` (dark) |
| Ink | `#1E1B4B`, `#09090B`, `#450A0A`, `#134E4A` | `#111110` / `#F2EFE9` |
| Style | Claymorphism (chunky, bubbly, 16–24px radii, double shadows) | Minimalism & Swiss / NEXUS editorial (flat, ruled, geometric) |
| Pattern | Feature-Rich Showcase, Hero-Centric (card grids, CTA repetition) | Masthead + numbered rows + hairline rules |
| Fonts | Baloo 2/Comic Neue, Newsreader/Roboto, Outfit/Work Sans (Google Fonts) | System Bengali + system Latin only (no bundled files) |
| Radii/shadows | Card 12–16px, multi-level shadow scale | News 0px/no shadows; learning 12px/one soft shadow |
| Dark mode | "Avoid dark mode for this product" (Claymorphism deal) | Full dark theme with its own token column |
| Buttons | Blue primary `#1E40AF` (persisted deal) | Red `#B4232A` fill, white text |
| Theming | `ColorScheme.fromSeed()` example | Explicit fixed hex tokens in `app_theme.dart` |

## Files produced (this stage only — no `app/` file touched)

- `~/workspace/sarangsho-plus/design-system/sarangsho-plus/MASTER.md`
  (reconciled NEXUS design system, §§0–15)
- `~/workspace/sarangsho-plus/design-system/sarangsho-plus/tokens.json`
  (DTCG, valid JSON, light + dark, type/spacing/radius/motion/shadow)
- `~/workspace/sarangsho-plus/design-system/sarangsho-plus/RECONCILIATION.md`
  (this file)
- `~/workspace/sarangsho-plus/design-system/sarangsho-plus/pages/` —
  empty directory created by the persist tool; no page overrides yet
  (Stage 2+ may add them).

## Addendum — centralized shape system (2026-11-18, Rudro requirement)

Rudro added one requirement after Stage 1 was first delivered: a
centralized shape system — one design-token layer for all boxes/rounds/
corners/buttons/shapes, default box, variants on demand, no per-screen
hardcoding, no repeated app-code updates.

- Added as `MASTER.md` §3.4 ("Shape system — centralized") and as a
  `shape` group in `tokens.json` (default + 6 variants + 6 roles:
  card, button, chip, banner, dialog, input).
- Reconciliation: the NEXUS radii from REDESIGN_PLAN.md §2.3 (news
  0–4px, learning max 12px, chips 999, sheets 16 top corners) **became
  the shape tokens' values** — `AppShapes` is a semantic layer on top of
  the raw `AppRadii` numbers, not a competing system. No value was
  changed; the shape system only names and centralizes them.
- No conflict with any skill deal arose here: the skill's generic card
  radius/shadow scale had already been rejected in favour of NEXUS (§3.3
  of MASTER.md), and the shape system inherits that choice.

## Addendum — 2.0 palette override (2026-11-18, Rudro)

Rudro set the 2.0 app palette from his screenshot on 18 Nov 2026,
00:48: **Forest Green `#1E3A2B`** (primary/deep), **Oat `#EEE6D6`**
(light background/surface), **Flamingo Pink `#FF7AB8`** (restrained
accent). This **replaces the NEXUS red-black-white palette**
(cool crimson `#B4232A` / `#E5484D` on true white `#FFFFFF`) that
Stage 1 reconciled and Stage 2 implemented.

- What changed: colours only. `MASTER.md` §1 rewritten (light + dark
  token tables, contrast notes); `tokens.json` colour values updated
  (old `red`/`red-soft`/`warning` keys removed; `forest`, `pink`,
  `pink-text`, `pink-light`, `forest-light` added); `AppColors` in
  `app/lib/widgets/app_theme.dart` re-tokenized; every call site
  split into primary fills (`primaryFor`: forest / lighter forest
  `#2F5442`, white text) vs text accents (`accentFor`: darkened pink
  `#9E2A5C` on light / lightened pink `#FF9ECB` on dark) vs non-text
  pink pops (raw `#FF7AB8`: dots, indicator bars, progress, switch
  track, selected-option border).
- What did NOT change: the NEXUS layout/component system — numbered
  rows, masthead, hairlines, type scale, spacing, radii, shapes
  (`AppShapes`), components. No screen was restructured for the
  palette; no new hue was introduced. Success is now a forest shade,
  error a pink shade, medium relevance a neutral — the old state
  colours (success green `#1E7A46`, error red `#B3261E`, amber
  `#9A6A12` / `#D9A441`) are deleted.
- Why the split was needed: raw pink on oat is 1.94:1 and white on
  raw pink is 2.41:1, so raw pink can never be text or a fill behind
  white text. The derived shades are the same hues: darkened pink
  `#9E2A5C` is 5.76:1 on oat; lightened pink `#FF9ECB` is 8.31:1 on
  the dark forest paper. Every text/background pair in both modes
  verifies ≥4.5:1 (`app/tools/check_palette_contrast.py`, exit 0).
  Two captions were darkened to pass: light `inkFaint` `#8A847C` →
  `#6B6357` (2.98:1 → 4.77:1 on oat); dark `inkFaint` `#8A857C` →
  `#BFB69E` (4.86:1 on the dark soft surface).
- Dark mode base is Forest Green (`#14261C` paper, `#1E3A2B` surface,
  `#2A4A3A` soft surface); Oat becomes the light text/surface tone
  there (`#EEE6D6` ink).
- Known interim concern (for the Story stage, not Stage 3): the
  Story screen's tokens (`storyAccent` → forest, `storyAccentDark` →
  `forestLight`) were mapped to the primary because that screen uses
  the accent as a FilledButton background behind white text. Its
  small dark-mode label text against `forestLight` is ~2.10:1 on the
  warm dark story paper — the Story stage must split the story
  screen's text and fill accents when it restyles that screen.
  The Story screen itself was not touched in this change.
