# Sarangsho Plus — Design System (NEXUS editorial system)

> **LOGIC:** When building a specific page, first check `design-system/sarangsho-plus/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.
>
> **Project:** Sarangsho Plus — Flutter app (`~/workspace/sarangsho-plus/app/`,
> package `com.sarangsho.plus`, v1.3.0+2014), Bengali-first BCS/Bank exam
> learning app, offline, no network at runtime.
> **Direction:** NEXUS editorial system, approved by Rudro 8 Nov 2026.
> Full spec: `~/workspace/sarangsho-plus/REDESIGN_PLAN.md` §2 (this file is
> the design-system rendering of that spec; the plan governs on any
> disagreement).
> **Generated:** 2026-11-17 via ui-ux-pro-max `--design-system`
> (`"news reading editorial minimal"`); **reconciled to NEXUS:** 2026-11-18.
> **Palette override 2026-11-18 (Rudro):** Forest Green / Oat /
> Flamingo Pink replaces the NEXUS red-black-white palette (§1).
> The NEXUS layout/component system stays; only colours changed.
> **Category:** News/Media Platform + Education (exam learning).
> **Token files:** `tokens.json` (W3C Design Tokens Community Group JSON,
> light + dark). Token files are master-level only; `--page` overrides do
> not emit tokens.
> **Reconciliation:** see `RECONCILIATION.md` (same directory) and §0 below.
> **Scope:** visual / layout system only. No new data, features, screens,
> packages, font files, or network calls. Tokens live in
> `app/lib/widgets/app_theme.dart` (`AppColors`, `AppSpacing`, `AppRadii`,
> `AppShadows`, `AppMotion`, `AppType`, `buildLightTheme()`,
> `buildDarkTheme()`).

---

## §0. Reconciliation — skill deal vs NEXUS (NEXUS wins on every conflict)

The ui-ux-pro-max searches returned four design-system deals plus Flutter
stack guidance. Each was kept only where it agreed with the approved NEXUS
spec in `REDESIGN_PLAN.md` §2; on every material conflict NEXUS wins.
Full per-search record: `RECONCILIATION.md`.

**Agreed (kept from the skill):**
- Minimalism & Swiss Style (2 of 4 searches): clean, geometric, high
  contrast, grid-based, white space, type-led hierarchy — this *is* the
  NEXUS spirit, and it validates the direction.
- Flat Design effect rule "no gradients/shadows, clean lines,
  typography-focused" — matches NEXUS (no gradient fills, no shadows on
  news screens).
- Newsreader/Roboto pairing's *mood* (news, editorial, trustworthy,
  readable) — the editorial intent is right, even though the fonts
  themselves cannot be used (see below).
- Skill rules kept wholesale: ≥44px touch targets (48dp Android), body
  text never below 12px, 4.5:1 contrast minimum, no emoji as icons,
  vector/Material icons only, consistent icon sizing, 8dp spacing rhythm,
  visible focus/disabled states, reduced-motion + large-text support,
  safe-area compliance, token-driven theming (no hardcoded hex in
  components), one motion curve family with shared durations.
- Flutter stack guidance: use `ColorScheme`/`ThemeData`, never hardcoded
  colours in widgets — matches the plan (tokens in `app_theme.dart` only).
  Note: the skill's `ColorScheme.fromSeed()` example is NOT used — NEXUS
  tokens are explicit fixed hex values, not seed-derived.

**Differed — NEXUS chosen (see RECONCILIATION.md for the full table):**
- Accent colour: skill dealt indigo `#4F46E5` + orange `#EA580C`
  (Claymorphism), pink `#EC4899` (Swiss deal), teal `#0D9488` + amber
  `#D97706` (Flat deal), and red `#DC2626` + blue `#1E40AF` (persisted
  deal). **Chosen: cool crimson `#B4232A` (light) / `#E5484D` (dark),
  hue ≈ 357°, no orange, no blue, no pink, no teal.** `#DC2626` was the
  closest deal but is warmer/brighter than the approved crimson.
- Background: skill dealt tinted backgrounds (`#EEF2FF`, `#FEF2F2`,
  `#F0FDFA`, `#FAFAFA`). **Chosen: true white paper `#FFFFFF`** —
  newspapers are white, not warm/tinted paper; warm paper `#FAF8F3`
  is retired.
- Style: Claymorphism (chunky, bubbly, thick borders, 16–24px radii,
  double shadows) and the "Feature-Rich Showcase" / "Hero-Centric"
  patterns (feature grids, card dashboards, CTA repetition) were
  **rejected outright** — they are the exact card-heavy dashboard the
  redesign removes. News screens are numbered rows + hairline rules,
  not cards.
- Typography: Baloo 2 / Comic Neue (playful, kids) and Newsreader /
  Roboto (Google Fonts) were **rejected as fonts** — no new font files
  may be bundled (APK size budget) and the app must work offline.
  **Chosen: system Bengali + system Latin fonts only**; hierarchy by
  weight + size + spacing, never by colour alone. The editorial *mood*
  of Newsreader/Roboto is the intent to approximate with weight/size.
- Radii/shadows: skill's generic card radius 12–16px + multi-level
  shadow scale were **replaced** by the NEXUS split (news 0–4px, no
  shadows; learning max 12px, one soft shadow only on flashcard +
  quiz-ring card).
- Dark mode: Claymorphism deal said "avoid dark mode for this product".
  **Rejected** — the app ships a full dark theme (persisted setting),
  with its own token column below.

---

## §1. Colour tokens

> **Palette override (Rudro, 2026-11-18):** Forest Green `#1E3A2B`
> (primary/deep), Oat `#EEE6D6` (light paper/surface), Flamingo Pink
> `#FF7AB8` (restrained accent only). This REPLACES the NEXUS
> red-black-white palette (`#B4232A` crimson, white paper) from
> REDESIGN_PLAN.md §2.1. Layout, type, spacing, radii, shapes and
> components are unchanged — only the colours changed. See
> RECONCILIATION.md (addendum, 2026-11-18) for the full record.
> Palette discipline: these three hues plus their tints/shades plus
> neutral text colours only — no new hues. Success is a forest shade,
> error a pink shade, medium relevance a neutral.

### 1.1 Light mode (Oat paper)

| Token | Light | Use |
|---|---|---|
| `forest` | `#1E3A2B` — Forest Green, **the primary** | Fills with white text: logo block, numeral block, square arrow buttons, icon tiles, primary buttons, "জানি" button, done tracker squares, ≥80% quiz ring arc. Also success forest (state colour) and forest text where a dark accent is needed. Never a text colour on a forest background. |
| `forestLight` | `#2F5442` — lighter forest | Dark-mode primary fill only (see §1.2). Not used in light mode. |
| `oat` | `#EEE6D6` — Oat | Light paper + surface. Surfaces are distinguished by hairlines, not fills. |
| `oatSoft` | `#F5EFE0` — lighter oat tint | Learning surfaces only (`LearnSurface`, flashcard back, quiz option unselected, revision rows). Never on news screens. |
| `pink` | `#FF7AB8` — Flamingo Pink, raw | **Non-text pops only:** dots, 2–3px indicator bars, progress value, switch track when on, selected-option border, open-row left edge, refresh spinner. Never a large surface, never body text (1.94:1 on oat), never behind white text (2.41:1). |
| `pinkText` | `#9E2A5C` — darkened pink | **The text accent on light.** Numerals `01`–`04`, category labels, active nav item + label, search highlight, quiz mode label, flashcard front headword, "পড়া হয়েছে" state, error text. 5.76:1 on oat, 6.23:1 on `oatSoft`. |
| `pinkLight` | `#FF9ECB` — lightened pink | Dark-mode text accent only (see §1.2). Not used in light mode. |
| `pinkSoft` | `#F9DCE8` | Rare light pink tint. |
| `ink` | `#111110` (near-black, not pure `#000`) | Headlines, body, primary text. 15.23:1 on oat. |
| `inkSecondary` | `#5C564E` | Summaries, secondary text. 5.84:1 on oat. |
| `inkFaint` | `#6B6357` (darkened 2026-11-18) | Captions, dates, hints. 4.77:1 on oat — the old `#8A847C` was 2.98:1 on oat and failed WCAG. |
| `hairline` | `#B5A67F` | 1px separators — the system's main structuring device. Darker than the old `#E3DED6`, which was invisible on oat. |
| `hairlineStrong` | `#111110` (ink) | 2px rule under the masthead; 1px ink rule above the footer of a story row group. Sparingly: masthead, section headers, detail header. |
| `success` | `#1E3A2B` (= `forest`) | Correct answers, "পড়া হয়েছে ✓", quiz ring at ≥80%. Small text/icons only. A forest shade — no new hue. |
| `error` | `#9E2A5C` (= `pinkText`) | Wrong answers, load error. A pink shade — no new hue. Distinguish correct/wrong by icon + label, never by shade alone. |

### 1.2 Dark mode (Forest base)

| Token | Dark | Notes |
|---|---|---|
| `darkPaper` | `#14261C` — darker forest shade | App background. Full dark theme, not an inversion. |
| `darkSurface` | `#1E3A2B` (= `forest`) | Learning surfaces, sheets, dialogs. |
| `darkSurfaceSoft` | `#2A2A26` → `#2A4A3A` (lighter forest tint) | Flashcard back, quiz option unselected, revision rows. |
| `forestLight` | `#2F5442` | Primary fill in dark (logo block, arrows, tiles, primary buttons). White text on it is 8.51:1. |
| `pink` | `#FF7AB8` | Non-text pops, as in light mode. 6.59:1 vs dark paper as a bar/dot. |
| `pinkLight` | `#FF9ECB` | **The text accent on dark.** Numerals, labels, active nav, highlight. 8.31:1 on dark paper, 5.14:1 on `darkSurfaceSoft`. Raw pink is 4.08:1 on `darkSurfaceSoft`, so it is never text there. |
| `darkInk` | `#EEE6D6` (= `oat`) | Primary text. 12.79:1 on dark paper. |
| `darkInkSecondary` | `#CFC6B2` (muted oat) | Secondary text. 9.35:1 on dark paper. |
| `darkInkFaint` | `#BFB69E` (dim oat) | Captions, hints. 6.70:1 on dark paper, 4.86:1 on `darkSurfaceSoft`. |
| `darkHairline` | `#33503F` | 1px separators — must stay visible in dark mode. |
| `hairlineStrong` | `#EEE6D6` (oat) | 2px rule under masthead, etc. |
| `successLight` | `#7FB89A` | Correct / ≥80% ring (dark). 6.97:1 on dark paper. |
| `darkError` | `#FF9ECB` (= `pinkLight`) | Wrong answers, load error (dark). |

### 1.3 Contrast notes (verified — `app/tools/check_palette_contrast.py`)

- Forest `#1E3A2B` on oat ≈ **9.98:1**; white on forest ≈ **12.39:1**; white on `forestLight` ≈ **8.51:1**.
- Pink `#FF7AB8` on oat ≈ **1.94:1** and white on pink ≈ **2.41:1** — raw pink is never text and never behind white text. That is why the text accent is the darkened `#9E2A5C` (5.76:1 on oat) in light mode and the lightened `#FF9ECB` (8.31:1 on dark paper) in dark mode.
- Ink `#111110` on oat ≈ **15.23:1**. `inkSecondary` on oat ≈ **5.84:1**. `inkFaint` `#6B6357` on oat ≈ **4.77:1** (darkened from `#8A847C`, which was 2.98:1 on oat).
- Primary button: white 15px w700 text on forest (light) / `forestLight` (dark) — both ≥8.5:1.
- Correct/wrong are distinguished by icon (`check_circle` vs `cancel`) + label, never by shade alone (forest vs darkened pink are close in darkness).
- Dark mode: normal text contrast ≥4.5:1 on dark surfaces; 3:1 is only for large text or non-text UI. Check dark contrast independently — never assume light-mode values carry over. All gated text pairs are checked by `tools/check_palette_contrast.py` (exit 0 = all ≥4.5:1).
- **Deleted tokens (grep must return zero):** `red`, `redLight`, `redDark`, `redSoft`, `amber`, `amberSoft`, `darkAmber`, `amberFor`, plus the old state colours `deepGreen`, `greenSoft`, `darkGreenSoft`, `emeraldLight`, `emeraldMid`, `deepGreenDark`, `success #1E7A46`, `error #B3261E`. `AppColors.accentFor(brightness)` keeps its signature but now returns the **text** accent (`pinkText` / `pinkLight`); fills use the new `primaryFor(brightness)` (`forest` / `forestLight`).

## §2. Typography

System Bengali font (no new font dependency — the device's Bengali font
renders the text; **do not bundle Noto Sans Bengali** — megabytes, breaks
the size budget). Latin (English headwords, IPA, numbers) uses the same
system Latin font. Hierarchy is by **weight + size + spacing**, never by
colour alone. No Google Fonts import — the app is offline.

### 2.1 Font pairing

| Role | Font | Notes |
|---|---|---|
| Bengali (all UI copy, headlines, body) | System Bengali font | Device-rendered; no file bundled. |
| Latin (headwords, IPA, numerals, English UI) | System Latin font | Same system stack; headwords are **never** translated, never Bengali font. |
| Numerals (`01`, `02`…) | Latin digits, tabular, w900, pink | NEXUS numerals are Latin by design; edition dates use `formatEditionDate` (Bengali month names, Latin digits — unchanged). |

### 2.2 Type scale (`AppType` — keep field names, add `masthead`, `numeral`, `headword`, `headwordLarge`, `ipa`)

| Token | Size / height / weight | Use |
|---|---|---|
| `masthead` | 30px / 1.1 / w900, letter-spacing −0.5 | App wordmark "সারাংশ প্লাস" in the top bar. One place only. |
| `display` | 28px / 1.15 / w900, −0.3 | Top-story headline (hero); story-detail headline 26px. |
| `headline` | 22px / 1.3 / w800 | Story-row headline; quiz question 20px (kept). |
| `title` | 20px / 1.25 / w800 | Screen titles (English, Quiz, Library, Profile header). |
| `section` | 17px / 1.35 / w800 | Section headings inside story detail; "আজকের পড়া". |
| `body` | 16px / 1.6 / w400 | Story summary + detail body (Bengali needs 1.6; do not tighten). |
| `bodySmall` | 14px / 1.6 / w400 | Summaries in rows, word-card body, mistake text. |
| `caption` | 12px / 1.4 / w400 | Dates, sources, hints. |
| `label` | 12px / 1.4 / w700, letter-spacing +0.6, **uppercase for Latin only** | Category labels, "প্রধান খবর", relevance. Bengali labels are **not** uppercased (Bengali has no case) — use weight + spacing instead. |
| `numeral` | 40px / 1.0 / w900 (hero: 64px) | `01`–`04` story numerals. Latin digits, pink, tabular. |
| `headword` | 22px / 1.3 / w800, Latin, letter-spacing 0 | English headword in collapsed row + word card. |
| `headwordLarge` | 34px / 1.2 / w800, Latin | Flashcard front headword (keep today's 34px). |
| `ipa` | 15px / 1.5 / w400, Latin | IPA + Bangla phonetic. |

### 2.3 Type rules

- Bengali body minimum **14px**; captions minimum 12px; **nothing below
  12px** (the old 11px offline pill text becomes 12px).
- Line height: Bengali body 1.6, Bengali headings 1.15–1.3, Latin
  headwords 1.2–1.3. Do not set a Bengali heading below 1.15 — vowel
  signs clip.
- **200% text scale:** the existing test (Home at 200%, no overflow)
  must keep passing, extended to the numbered row, the word row and the
  quiz runner. Design for it: numerals are fixed-width Latin digits,
  headlines wrap (`maxLines` none in rows — rows grow vertically, never
  overflow horizontally), the top bar collapses the tagline first,
  section chips scroll horizontally.
- Numbers in Bengali UI: counts (`14 খবর`) stay as today; story numerals
  are position numbers (`01`, `02`… — the story's position in the
  *current list*, 1-based, `%02d`; **not** the story id `CA01`).
- Short labels only (existing copy rule). No new explanatory paragraphs.
- `textTheme` mapping in `buildLightTheme` / `buildDarkTheme` is unchanged.

---

## §3. Spacing, grid, separators, radii, shapes, shadows

### 3.1 Spacing — 8pt grid, kept (`AppSpacing`)

| Token | Value | Usage |
|---|---|---|
| `s4` | 4px | Tight gaps |
| `s8` | 8px | Icon gaps, inline spacing, vertical gap between learning items |
| `s12` | 12px | Small gaps, numeral-to-text gap in rows |
| `s16` | 16px | Screen side padding; standard padding; row vertical padding |
| `s24` | 24px | Section gaps (`sectionGap = 24`) |
| `s32` | 32px | Large gaps |
| `s48` | 48px | Largest gaps |
| `screen` | 16px | Screen side padding (stays 16px) |
| `sectionGap` | 24px | Gap between sections |

News rows: 16px side padding, 16px vertical padding, **0px card margin** —
the row *is* the layout.

### 3.2 Separators (the new structuring device)

- `Divider` / `BorderSide` 1px `hairline` between story rows.
- 2px ink rule under the masthead and above the "সবগুলো" section header;
  1px `hairlineStrong` under each screen title on learning screens.
- No shadow is used to separate news rows.

### 3.3 Radii (`AppRadii` — `card = 20` is DELETED)

| Token | Value | Usage |
|---|---|---|
| `news` | 0px | News system everywhere. Numeral block 0px (square). Arrow button 0px (square, 40×40). Category label 0px (plain text, no pill). Bottom nav 0px. |
| `learn` | 12px | `LearnSurface` radius 12. |
| `button` | 8px | Buttons radius 8. |
| `sheet` | 16px | Bottom sheets, top corners only. |
| `chip` | 999px | Chips stay pills — the one round element, learning contexts only. |
| Search field | 4px | The one 4px radius in the news system. |
| Share card (rendered PNG) | 4px | White card, 1px ink border. |

### 3.4 Shape system — centralized (added 2026-11-18, Rudro requirement)

One design-token layer owns **every** box, round, corner, button and
shape in the app. It lives hidden in the token/theme layer — no screen
hardcodes its own radii or padding, and no repeated app-code updates are
needed to change a shape. **Changing a shape in one place updates
everywhere.** This is not a competing system to the NEXUS radii in §3.3:
the NEXUS values (REDESIGN_PLAN.md §2.3) **are** the shape tokens'
values — `AppShapes` is the semantic layer on top of the raw `AppRadii`
numbers, and the two can never drift apart.

#### How it is built (implementation contract for later stages)

- New class `AppShapes` in `lib/widgets/app_theme.dart`, next to
  `AppRadii` / `AppSpacing`. It holds one static `ShapeRole` per role
  below (radius + padding + border + shadow, all read from `AppColors` /
  `AppRadii` / `AppSpacing` — never a literal number).
- Every component and screen takes its shape from an `AppShapes` role
  (or the default) — never `BorderRadius.circular(...)`, never a
  hard-coded `EdgeInsets` for a shape's padding. Theme-level widgets
  (`buttonTheme`, `inputDecorationTheme`, `dialogTheme`,
  `bottomSheetTheme`, `chipTheme`) read their shapes from `AppShapes`
  too, so the theme and the components agree by construction.
- **One-line change test:** editing one value in `AppShapes` must change
  every use of that role across all five tabs with no other file edited.
  A new shape need is met by adding a role or a variant to `AppShapes`,
  never by inlining a radius on a screen.

#### The one default shape: box

The default shape is the **box** — square corners, radius 0. It is what
a component gets when it asks for no variant, and it is used most of the
time: every news surface, every row, every tile, the masthead logo block,
the numeral block, the square arrow button, the bottom nav. If a screen
does not need a different shape, it uses the box and says nothing.

#### Shape variants (on demand only)

| Variant | Radius | When it is used |
|---|---|---|
| `box` (default) | 0px | Everything, unless a role below says otherwise. |
| `small` | 4px | Search field, rendered share card. |
| `medium` | 8px | Buttons. |
| `soft` | 12px | Learning surfaces (`LearnSurface`, flashcard). |
| `round` | 999px | Chips — the one round element, learning contexts only. |
| `sheet` | 16px, top corners only | Bottom sheets and dialogs that slide from the bottom. |

#### Semantic shape roles

| Role | Default variant | Radius / padding | Used for | On-demand alternative |
|---|---|---|---|---|
| `card` | `box` | 0px; 16px padding; 1px hairline separator, no shadow | News rows, story rows, saved-story rows — a "card" here is a ruled row, not a rounded card | `soft` (12px, `surfaceSoft`, no border/shadow) for learning surfaces: `LearnSurface`, collapsed word rows, phrase cards, revision rows, quiz mode/review/mistake items, Profile cards |
| `button` | `medium` | 8px; min height 48px; horizontal 16px / vertical 12px | Primary (`FilledButton`, forest fill), secondary (`OutlinedButton`, ink border), text button (no fill) | None — buttons are always `medium`; a 40×40 square arrow button is the `box` variant, not a button role |
| `chip` | `round` | 999px; horizontal 12px / vertical 8px | Font-size chips (Profile), search-recents `ActionChip`s, word-form / exam-type chips | None — chips are always round; the Home section filter is a text index, not chips |
| `banner` | `box` | 0px; full-bleed; 16px padding; 1px hairline below | Masthead block, `TopStoryHero` (forest numeral block + paper), story banner/hero image area on the explaining page (box, full-bleed) | `small` (4px) for the rendered share card PNG only |
| `dialog` | `medium` | 12px; 16px padding (24px for the share-preview dialog body) | Share-preview dialog, alerts | `sheet` (16px top corners) when the dialog is a bottom sheet |
| `input` | `small` | 4px; horizontal 16px / vertical 14px; 1px hairline border, focused 1.5px pink | Search field | None — inputs are always `small` |

#### Rules

- A screen that needs a shape it does not have asks `AppShapes` for a
  variant — it never invents a radius inline. If no existing role fits,
  add a role; do not reuse a wrong role (e.g. never use `chip` roundness
  to make a card look "friendly").
- The news/learning boundary (§12 rule 6) applies to shapes too: news
  screens use `box` (and `small` for the search field); learning screens
  use `soft` cards and `round` chips. A word row must never look like a
  news row, and a news row must never look like a flashcard.
- `AppRadii.card = 20` stays deleted. No new `Card` widget anywhere.
  The old `PremiumCard` (radius 20 + shadow) is retired; its replacement
  is the `card` role (box on news, `soft` on learning).
- Shape tokens are theme-independent (same radii in light and dark);
  only their colours change per theme (§1).

### 3.5 Shadows (`AppShadows`)

- **News system: shadows deleted entirely** (`card` / `lifted` removed).
- **Learning system: one soft shadow only** (today's `card` shadow: blur
  16, offset 0/4, 6% black), and only on the flashcard and the quiz
  result ring card — nowhere else. Sheets keep the platform default.
- Elevation: `BottomNavigationBar` 8 → 0 (hairline top border instead).
  `AppBar` elevation stays 0.

---

## §4. Motion (`AppMotion` — unchanged)

- One curve `Cubic(0.16, 1, 0.3, 1)`; `fast` 180ms, `standard` 320ms,
  `page` 360ms; stagger 45ms steps (**cap 6 on Home**, was 8); fade +
  12px rise; hero headline transition preserved; flashcard 3D flip
  preserved (perspective 0.0015); score-ring 900ms count-up preserved.
- **One change:** numbered rows do not stagger on every rebuild — stagger
  only on first build of the list (guard with a `hasAnimated` flag or
  animate only `index < 6` on the initial edition load). Today
  `FadeSlideIn` re-runs whenever the list rebuilds (e.g. after a bookmark
  toggle), which makes rows visibly jump.
- Pressed feedback within 80–150ms (ripple/opacity); pressed-state
  visuals must not shift layout bounds or cause jitter.
- Reduced motion: disable hero parallax/stagger under reduced motion and
  render the static final state; respect the platform reduced-motion
  setting. No auto-rotating content.

---

## §5. Navigation components

### 5.1 Masthead (new, replaces the emerald hero header — Home S3)

White/paper background, 2px ink rule at the bottom. Row 1: forest square
logo block 40×40 with white "সা" (w900, 22px) + wordmark "সারাংশ প্লাস"
(`masthead` 30px w900, ink) + tagline "পরীক্ষার প্রস্তুতি, প্রতিদিন"
(12px, `inkSecondary`) — tagline sits under the wordmark on narrow
screens, not beside it. Row 2 (dateline): edition date in full
(`formatEditionDateLong`, 13px w700 ink) + "•" + "অফলাইন" (12px pink,
with `cloud_off` 14px icon) + edition switcher as plain text button
("সংস্করণ: ৮ নভেম্বর ২০২৬ ▾", 13px w700, pink chevron) opening the
existing dropdown as a bottom sheet. Search icon (24px, ink) at the
right end of Row 1, 48×48 target, opens Search. No gradient, no
watermark "সা", no large pink fills anywhere.

### 5.2 Bottom nav (restyled, same 5 tabs, same order, same labels)

White/paper background, 1px hairline top border, elevation 0. Active
item: pink icon + pink 12px w700 label + 24×3px pink indicator bar above
the label. Inactive: `inkFaint` icon + label. Icons unchanged (`home`,
`newspaper`, `edit_note`, `bookmark`, `person`, outlined/filled pairs).
48dp minimum touch height per item. 5 tabs stay — do not promote
English/Quiz to tabs.

### 5.3 In-app navigation

`AppBar`s: paper background, ink 18px w800 title, left-aligned, 1px
hairline bottom border (shared `NewsAppBar` widget or per-screen
`PreferredSize` hairline — `AppBarTheme` cannot draw it). Back chevron:
system default, ink. Actions (bookmark, share) stay as 48px
`IconButton`s.

### 5.4 Tab bars (English 3 tabs, Library 4 tabs)

Text tabs, no pills: active = pink 14px w800 + 2px pink underline
indicator; inactive = `inkSecondary` 14px; indicator full tab width;
background paper; divider hairline under the bar.

---

## §6. Buttons, inputs, pills

| Element | Spec |
|---|---|
| Primary button (`FilledButton`) | Forest `#1E3A2B` fill, white text 15px w700, radius 8, min height 48, full-width where today full-width. Dark: `#2F5442` fill, white text (verify §1.3). |
| Secondary button (`OutlinedButton`) | 1.5px ink border, ink text, radius 8, min height 48. |
| Text button | Pink text 14px w700, no background. |
| Disabled button | Hairline fill + `inkFaint` text, explicitly set — disabled must be visibly non-interactive. |
| Square arrow button (NEW, news only) | 40×40, solid forest, white `arrow_forward` 20px, radius 0. 48×48 hit area via padding. |
| `ChoiceChip` (section filter) | **Retired on Home** (section filter becomes a text index, §8). Kept only for font-size (Profile) and `ActionChip` for search recents: unselected = paper + hairline border + ink text; selected = ink fill + white text (font-size) / pink text + pink border (recents). No pink tint. |
| `MetaPill` (replaces `StatusPill`) | Square (radius 2), 1px hairline border, paper background, ink 12px w700 text, optional 13px icon. No tint fill. |
| Text field (search) | Paper fill, 1px hairline border, radius 4, focused border 1.5px pink, 14px vertical padding, search icon ink. |
| `SegmentedButton` (language) | Unselected: paper + hairline; selected: ink fill + white text ("বাংলা" / "English"). |
| `Switch` (dark mode) | Track: hairline when off, pink when on; thumb white. |
| Progress bars (quiz, revision, flashcards, reading) | Track `hairline`, value **pink**, 6px (reading bar stays 3px). Quiz ring: pink arc, hairline track. |

---

## §7. News components (editorial system — Home, Timeline, Editorial, Search results, Saved stories, Story detail)

### 7.1 `NumberedStoryRow` (replaces `StoryCard._standardCard`; keep the `StoryCard` class name/API)

Full-width row, paper background, **no card, no shadow, no radius**.
Left → right: pink numeral (`01`, `02`… position in current list) 40px
w900 pink, top-aligned; 12px gap; middle column (expanded): category
label (12px w700 pink, +0.6 spacing) line 1; headline (`headline` 22px
w800 ink, height 1.3, `Hero` preserved) line 2; summary (`bodySmall`
14px/1.6 `inkSecondary`, max 3 lines, ellipsis) line 3; meta line
(12px `inkFaint`: date • first source publication • relevance mark)
line 4. Right column: square forest arrow button (40×40) vertically
centred on the headline block. Bookmark is **removed from the row** —
bookmarking happens on the detail page and by long-press on the row
(`onLongPress` → toggle bookmark + snackbar reusing
`bookmark`/`removeBookmark` strings — the only new interaction).
Row padding 16px vertical, 16px horizontal; 1px hairline `Divider`
under each row (none after the last). Tap anywhere → detail. Search
highlight: matched text in the headline becomes pink w800 (via
`HighlightText`, accent now pink) — no background tint.

### 7.2 `TopStoryHero` (replaces `StoryCard` hero + emerald cover)

Asymmetric NEXUS layout. Left: solid forest block, width ~96px, full height
of the hero, containing the giant numeral `01` (64px w900 white,
top-aligned) + "প্রধান খবর" (12px w700 white, +0.6) stacked vertically
under the numeral, left-aligned, **no rotation** (rotation breaks Bengali
legibility). Right: paper background, 16px padding: category label (pink),
headline (`display` 28px w900 ink), summary (14px/1.6, max 3 lines), meta
line (date • sources), forest square arrow button at the bottom right of the
text block. 2px ink rule above the hero, 1px hairline below. No gradient,
no "প্রধান খবর" pill, no white-on-pink text. Hero is story #1 **only
when the filter is "সবগুলো"**; when a hero is shown, list rows are
numbered `i + 2`, otherwise `i + 1`.

### 7.3 `NewsSectionLabel` (replaces `SectionHeading` on news screens)

Small pink label (12px w700, +0.6 spacing) above an ink 17px w800 heading,
with a 1px hairline under the pair. Used for "আজকের সংস্করণ — ৮ নভেম্বর
২০২৬", story-detail section headings, Library tab titles. Learning
screens use `LearnSectionLabel` instead (§9).

### 7.4 `RelevanceMark` (replaces `ScoreBadge`)

No pill, no star, no tint. Inline text: `● উচ্চ` (pink, w700) /
`● মাধ্যমিক` (neutral, w700) / `● কম` (faint) / omitted entirely when no
relevance label (today's "—" pill becomes *nothing*). The full raw
`examRelevance` text stays as a tooltip / on the detail page under
"পরীক্ষার গুরুত্ব". **No numeric 0–100 score anywhere** (relevance is a
label only).

### 7.5 Dates, sources, share card

- Date/time: one format everywhere — `formatEditionDate` for edition
  dates; story dates shown verbatim from the data (do not reformat
  free-text dates). Meta line order, fixed: `date • source • relevance`.
- Sources sheet: bottom sheet, radius 16 top corners only, drag handle
  (40×4, `inkFaint` 50%), title "সূত্রসমূহ" (`NewsSectionLabel`),
  `ListTile`s with forest square 32×32 leading tile (white `article` 18px
  icon), title 15px w700, subtitle 13px `inkSecondary`, trailing
  `open_in_new` 18px ink when a URL exists; 1px hairline between items.
  Empty sources: one-line "এই খবরের কোনো সূত্রের তথ্য নেই" in
  `inkSecondary` 14px **with** the "সূত্রসমূহ" label above it.
- Share card (rendered PNG): white card, radius 4, 1px ink border: top
  band white with a 4px forest rule at the very top; wordmark "সারাংশ প্লাস"
  16px w900 **ink** + date 12px `inkSecondary`; headline 19px w800 ink;
  summary 13px/1.6, max 4 lines; footer: relevance mark (`● উচ্চ`, pink)
  + first source (italic, `inkFaint`). Preview dialog: custom dialog,
  paper background, radius 12, no large pink fills; actions "বন্ধ করুন" (text, ink)
  + "শেয়ার করুন" (filled forest). Rendering (3.0 pixel ratio,
  `RepaintBoundary`, cache dir, text fallback) unchanged.

---

## §8. Home layout (flagship — build first)

Top → bottom: Masthead (logo block + wordmark + tagline / dateline +
offline + edition button + search icon) — 2px ink rule — search field
(16px margins, 48px row, hairline border, radius 4) — English row —
Quiz row — 1px hairline — "আজকের সংস্করণ — ৮ নভেম্বর ২০২৬"
(`NewsSectionLabel`, 17px w800 ink) + coverage line (12px `inkFaint`)
— section index (horizontal scroll text items: "সবগুলো" + six Bengali
section names, 14px, active = pink w800 + 2px pink underline, inactive =
`inkSecondary`; no chips, no pills, no tint) — 2px ink rule —
`TopStoryHero` (only when filter = "সবগুলো") — numbered rows `02…`
— 24px bottom space. Pull-to-refresh kept (`RefreshIndicator`, pink).

- Stats strip deleted as a component — counts move into the dateline
  ("১৪ খবর • ২০ শব্দ • ২৫ প্রশ্ন", 12px `inkFaint`) and into the
  English/Quiz entries.
- English + Quiz entries become two **text rows** (not cards):
  hairline-separated, 56px min height, forest square 40×40 icon tile
  (`translate` / `quiz_outlined`, white icon on forest) + title 16px w800
  ink + counts 12px `inkSecondary` + forest square arrow 32×32 at the right.
- Edition switcher: text button opening a bottom sheet listing all
  editions (date + counts + status, hairline separators, selected row =
  pink date + pink check). Replaces the `DropdownButton`.
- Greeting ("শুভ সকাল") moves into the masthead dateline area as 13px
  `inkSecondary`, or is dropped if it crowds the dateline at 200% scale.
- "Recent news" = Home story list + Timeline (S4). "Categories" = the six
  sections as the Home section index. No separate Categories screen.

---

## §9. Learning components (premium language-learning feel — do NOT force newspaper layouts here)

News rows are numbered and ruled; learning screens are calm, spacious and
tactile. The two systems share tokens (forest/pink, ink, paper, 8pt grid, motion)
but **different components**. A word row must never look like a news row,
and a news row must never look like a flashcard.

### 9.1 `LearnSurface` (new, replaces `PremiumCard` on learning screens)

`surfaceSoft` (`#F4F2EE`) background, radius 12, **no border, no shadow**.
Used for: collapsed word rows, phrase cards, revision rows, quiz mode
cards, quiz review items, mistake items, streak/tracker/editions/GK/about
cards on Profile. Padding 16px; vertical gap 8px between items.

### 9.2 `LearnSectionLabel`

13px w800 **ink** label (no pink, no rule); screen-level headings on
learning screens ("আজকের পড়া", etc.).

### 9.3 Collapsed word row (English `_WordList` — the single most-tapped row)

`LearnSurface`, 12px vertical / 16px horizontal padding, min height 56px.
Left: headword (`headword` 22px w800, **ink** — pink is reserved for
accents; 20 pink headwords is noise) + Bangla meaning (14px,
`inkSecondary`, 1 line, ellipsis). Right: part of speech (12px,
`inkFaint`) + chevron (`keyboard_arrow_down`, ink, rotates 180° when
open). **New:** a 3px pink left edge (4px wide, full row height) appears
on the open row only. Bookmark state: small filled pink bookmark icon
(16px) at the right of the headword line when bookmarked. Tap →
expand/collapse (one open at a time, kept). Extracted as shared widget
`CollapsedWordRow` (used by English, Search, Library).

### 9.4 Expanded word card (`WordCard` — same 11 items, same order, same honesty rules)

Container becomes `LearnSurface` with **0px horizontal margin inside the
list** (sits directly under its row, full-bleed within the 16px screen
padding, 1px hairline above — reads as the row unfolding, not a second
card). Section titles: 13px w800 **ink** + 24×2px pink rule *under* the
title. Body 15px/1.5. Headword 22px w800 ink + Bangla meaning 17px w700
ink. Bookmark `IconButton` 48px, bookmarked = filled pink icon. Chips
(word forms, exam types): paper background, 1px hairline border, radius
999, 13px ink text — **no pink tint**. Spelling row: doubled letters in
**pink** w700; letter spacing kept. Example: italic, quoted, 15px/1.5,
with a 2px pink left bar (4px wide). Absent items: italic 14px
`inkFaint`, unchanged copy ("তথ্য নেই" / "সরাসরি বিপরীত শব্দ নেই" /
"পূর্ববর্তী পরীক্ষার তথ্য নেই।"). Divider before source/relevance: 1px
hairline. "পুরো পাতা" button: outlined, ink border, radius 8.
`PhraseCard`: same system (phrase 19px w800 **ink**; Bangla meaning
16px w700 ink). All fields unchanged. Absent data is shown as absent —
never invented; only the 5 verified headwords carry a verified-pattern
note; no numeric scores.

### 9.5 Revision rows, flashcards, quiz

- Revision row (`_RevisionList`): `LearnSurface` row: headword 16px w800
  ink + Bangla meaning 14px; trailing compact **text button** "পড়া হয়েছে"
  (pink w700) / "পড়া হয়েছে ✓" (success forest w700, with the check — the
  one place forest survives as a *state* colour); tap target ≥48px high.
- Flashcard (`_FlipCard`): the one place a card *is* the content — paper
  background, radius 12, 1px hairline border, **one** soft shadow. Front:
  headword 34px w800 **pink**, IPA 16px `inkSecondary`, Bangla phonetic
  16px, flip hint 12px `inkFaint`. Back: headword 20px w800 ink, meaning
  19px w700 ink, synonyms 15px/1.6, example italic with pink left bar.
  Buttons: "জানি না" outlined ink; "জানি" filled forest. Done view: square
  88×88 forest tile, white check 44px; "শেষ!" 24px w900 ink.
- Quiz mode cards → `LearnSurface` + 48×48 square hairline tile, pink icon
  24px on paper; title 17px w800; subtitle 14px; note italic 12px
  `inkSecondary`; start button filled forest, full width. Option rows
  (`_OptionRow`): radius 8, unselected = paper + hairline border,
  selected = pink 1.5px border + pink 8% tint + pink radio dot with white
  check. Score ring (`_ResultView`): 180px, stroke 12px, track hairline,
  arc **pink** — except ≥80% where the arc is `success` forest; score 32px
  w900 ink; verdict 16px w800 (pink / forest at ≥80%). Review items:
  `LearnSurface`; correct = success forest icon + "সঠিক"; wrong = error
  pink icon + "ভুল". Quiz question carries a small pink mode/section label
  above it ("সংস্করণের কুইজ" / practice type label, 12px w700 pink, +0.6).
- Progress indicators: all `LinearProgressIndicator`s — track hairline,
  value pink, 6px, radius 4 (reading bar 3px, pink).
- Profile (learning system's home — uses `LearnSurface` throughout):
  logo = square 60×60 forest block, white "সা" 26px w900, radius 4; section
  headings → `LearnSectionLabel`; language `SegmentedButton` (§6);
  dark-mode switch pink-on; font-size chips selected = ink fill + white
  text; streak days 20px w900 **pink**; tracker = 7 squares 20×20 (done =
  solid forest square with white check; undone = hairline square, paper
  fill); editions rows hairline-separated, "ডাউনলোড করা" → `MetaPill`;
  GK stays "পরের সংস্করণে আসছে।" — do not dress it up into fake content.
  Language and Dark mode stay rows in this tab (not separate screens).

---

## §10. Empty states (one designed system — `EmptyState({icon, title, body, actionLabel?, onAction})`)

Centred column, 16px side padding; icon in a **square** 72×72, paper
background, 1px hairline border, pink icon 32px (no pink circle, no tint
fill); title 18px w800 ink; body 14px/1.6 `inkSecondary`, max 2 lines,
centred; optional action = outlined button (ink border, 48px). A hairline
rule (64px wide, 1px) sits between icon and title.

- Editorial: icon `edit_note`, title/body from existing strings; header
  "সম্পাদকীয়" (20px w800, hairline under) above the content; no action.
  Editorial stays empty until an opinion story exists in the data.
- Library tabs: icon per tab (`bookmark_outline` stories/words,
  `check_circle_outline` mistakes, `quiz_outlined` history); no action.
- Search, no query + no recents: icon `search`, body `typeToSearch`.
  Search, no results: icon `search_off`, body `noResults`.
- Flashcards, no words: icon `style_outlined`, body `noDataForWord`.
- Profile, no quiz history: one-line `noHistory` inside the streak card
  (a card state, not a screen state); streak card gets a 48px square forest
  flame tile.
- Home, no edition: `EmptyState(icon: newspaper, body: errorLoading)` +
  retry button wired to `_refresh`/`_boot`.

---

## §11. Icons

Material `Icons` only (no new icon font — size budget). Audit list (keep
the icon, change colour to ink/forest/pink per §1 unless noted): `home`,
`newspaper`, `edit_note`, `bookmark`/`bookmark_border`, `person`,
`search`, `clear`, `history`, `translate`, `quiz_outlined`,
`style_outlined`, `spellcheck_outlined`, `local_fire_department`,
`language`, `dark_mode`, `format_size`, `cloud_off_outlined`,
`article_outlined`, `open_in_new`, `open_in_full`, `share_outlined`,
`check`, `check_circle`, `cancel`, `radio_button_unchecked`,
`keyboard_arrow_down`, `arrow_forward`, `edit_note`. **Retire:** `star`
in `ScoreBadge` (replaced by `●` text in `RelevanceMark`); the 48px
green circle icon tiles (replaced by square hairline tiles with pink
icons). Icon sizes: nav 24, actions 24, list meta 14–16, empty state 32,
flashcard done 44. **No emoji as icons** (vector/Material icons only —
emojis are font-dependent and cannot be controlled via tokens).
Consistent icon family/style per hierarchy level; filled vs outline
discipline (one style per hierarchy level); stroke consistency.
Touch targets: every `IconButton` is already 48×48 by default — do not
wrap icons in smaller tap areas. Decorative icons beside visible text
are hidden from the accessibility tree; standalone icon controls have an
accessible name and expose selected/pressed/expanded state.

---

## §12. UX rules for this app

1. **Bengali-first.** All UI copy in Bengali by default; English map only
   via the Settings toggle. Headwords, IPA, synonyms, definitions,
   examples, collocations stay English (they *are* the learning content).
   Any new label needs both `stringsBn` and `stringsEn` entries.
2. **No unnecessary text.** Short labels only. No new explanatory
   paragraphs, no subtitles under empty states beyond the existing
   one-line bodies, no "welcome" copy.
3. **No oversized rounded cards.** News rows: radius 0, no card, no
   shadow. Learning surfaces: radius 12 max, no shadow except the
   flashcard (one soft shadow). `AppRadii.card = 20` is deleted.
   `PremiumCard` is deleted once migrated. No new `Card` widget anywhere.
4. **No excessive pink.** Pink is a restrained accent only (dots,
   indicators, small pops). Success is a forest shade, error a pink
   shade. Pink is never a background, brand colour, button fill (except
   the switch track), or header.
5. **No generic dashboard layouts.** No stats-strip cards, no grid of
   action cards, no "welcome" hero. Home is a masthead + rules +
   numbered list. Profile is a settings list, not a dashboard.
6. **News screens = editorial system; learning screens = premium
   learning feel.** Do not force newspaper layouts onto learning screens
   (no numerals on word rows, no hairline-only rows for quiz options, no
   forest-square-arrow on flashcards) and do not force learning chrome onto
   news screens (no `LearnSurface` on Home, Timeline, Editorial, Search
   results, Saved stories, Story detail). Search and Library are mixed
   screens — story parts are editorial, word parts are learning, and the
   two must look different on the same screen (that contrast is
   intentional).
7. **Mobile-first.** 48dp minimum touch targets (buttons, rows' tap
   areas, icon buttons, chips, tab items). No horizontal overflow at
   360px width or at 200% text scale. Horizontal scrolling allowed only
   for the section index and the tab bars (text, scroll by design).
8. **APK stays light (~17–20 MB arm64).** No new dependencies
   (`pubspec.yaml` deps stay `shared_preferences` + `url_launcher`). No
   font files, no image assets, no new native code.
9. **Forest + oat + pink is distinct from Sarangsho's orange-red.**
   Forest Green `#1E3A2B` is the primary, Oat `#EEE6D6` the paper,
   Flamingo Pink `#FF7AB8` a restrained accent — never orange-leaning,
   never a gradient, never a large pink fill. Typography (Bengali w900
   masthead, 40px numerals, hairline rules) and spacing (16px rhythm,
   ruled lists) are what make the app recognisable, not the pink alone.
10. **Do not invent.** No new data fields, no new screens, no shop /
    paywall / chatbot / login / ads / tracking, no "verified" claims
    beyond the 5 headwords, no numeric scores, no GK content, no
    editorial content. If a screen is empty in the data, design the
    empty state — do not fill it.
11. **Accessibility (skill priority 1–2, kept).** Contrast ≥4.5:1 for
    body text in both themes; colour is never the only indicator
    (correct/wrong by icon + label, not shade alone); screen-reader
    focus order matches visual order; form fields have labels, hints,
    clear errors near the field; disabled states are visually clear and
    non-interactive; dragging/swipe-only interactions have button
    alternatives (flashcards are button-driven `PageView`, no swipe);
    200% text scale and reduced motion supported without layout breakage.
12. **Performance.** No network at runtime (offline app — the redesign
    must not add any network call); lazy lists; reserve space to avoid
    layout shift; `FadeSlideIn` capped at first 6 items, first build only.

---

## §13. Anti-patterns (Do NOT Use)

- ❌ Card-heavy dashboard / stats-strip cards / feature-grid cards on news screens
- ❌ Crimson/red as brand colour, red gradients, red tints anywhere (retired 2026-11-18)
- ❌ Orange-leaning red, gradients, large pink fills, blue/teal accent colours
- ❌ Bundled font files / Google Fonts imports (offline app, APK size budget)
- ❌ Rounded cards (radius 20) and multi-level shadows on news screens
- ❌ Emojis as icons (use Material vector icons)
- ❌ Layout-shifting hovers / press states that move surrounding content
- ❌ Low-contrast text (below 4.5:1 for body) in either theme
- ❌ Instant state changes with no feedback (always 150–300ms, pressed feedback in 80–150ms)
- ❌ Invisible focus/disabled states
- ❌ Text below 12px; Bengali body below 14px; Bengali body line-height below 1.6
- ❌ Invented content (GK, editorial, exam claims, numeric scores)
- ❌ Hardcoded hex colours in components — all colour through `AppColors` / `ThemeData` tokens
- ❌ Cluttered layout; slow loading; horizontal scroll on mobile (except section index + tab bars)

---

## §14. Pre-delivery checklist (canonical — adapted from ui-ux-pro-max `references/pro-rules.md` for this app)

Stage 1 produces documents only — this checklist is for the later
implementation stages; do not claim it as done until code is delivered
and checked.

### Process
- [ ] Ran only searches relevant to the interface
- [ ] Reviewed `quick-reference.md` §1–§3 (CRITICAL + HIGH) as a final pass
- [ ] Tested on 375px (small phone) and in landscape orientation
- [ ] Verified behaviour with reduced-motion enabled and largest system text size (200%)
- [ ] Checked dark mode contrast independently (never assume light-mode values carry over)
- [ ] Confirmed all touch targets ≥44pt / ≥48dp and no content hidden behind safe areas

### Visual quality
- [ ] No emojis used as icons (Material vector icons only)
- [ ] All icons from a consistent family and style; filled vs outline disciplined
- [ ] Pressed-state visuals do not shift layout bounds or cause jitter
- [ ] Semantic theme tokens used consistently (no ad-hoc per-screen hardcoded colours)
- [ ] No pink anywhere except the restrained accent uses in §1 (dots, indicators, pops); no gradients; no card radius 20

### Interaction
- [ ] All tappable elements provide clear pressed feedback (ripple/opacity)
- [ ] Touch targets meet minimum size (≥44×44pt iOS, ≥48×48dp Android)
- [ ] Micro-interaction timing uses shared tokens (`AppMotion`)
- [ ] Disabled states are visually clear and non-interactive
- [ ] Screen reader focus order matches visual order; interactive labels descriptive
- [ ] Gesture regions avoid nested/conflicting interactions (long-press bookmark vs tap)

### Light/dark mode
- [ ] Primary text contrast ≥4.5:1 in both light and dark mode
- [ ] Normal primary and secondary text contrast ≥4.5:1 in both modes
- [ ] Dividers/borders and interaction states distinguishable in both modes
- [ ] Modal/drawer scrim measured against the real background; foreground legible
- [ ] Both themes tested before delivery (not inferred from a single theme)

### Layout
- [ ] Safe areas respected for headers, tab bars, bottom CTA bars
- [ ] Scroll content not hidden behind fixed/sticky bars
- [ ] Verified on small phone, large phone, tablet (portrait + landscape)
- [ ] Horizontal insets/gutters adapt by device size and orientation
- [ ] 8dp spacing rhythm maintained across component, section, page levels
- [ ] Long-form text measure readable on larger devices

### Accessibility
- [ ] Decorative icons beside visible text hidden from the accessibility tree
- [ ] Meaningful icons without equivalent visible text have a text alternative
- [ ] Icon controls have an accessible name and announce selected/pressed/expanded state
- [ ] Colour is not the only indicator
- [ ] Reduced motion and 200% text size supported without layout breakage
- [ ] 200% text scale: Home, numbered row, word row, quiz runner — no overflow (`takeException()` null)
- [ ] `flutter analyze` zero issues; `flutter test` green; arm64 APK 17–20 MB

---

## §15. Sources

- Approved spec: `~/workspace/sarangsho-plus/REDESIGN_PLAN.md` (NEXUS
  direction, token spec §2, screen plans §3, rules §4, tests §5).
- Skill: `~/workspace/custom-skills/ui-ux-pro-max/` — `SKILL.md`,
  `references/pro-rules.md`, `references/quick-reference.md`; search tool
  `scripts/search.py`. Search record + per-deal reconciliation:
  `RECONCILIATION.md`.
- Tokens: `tokens.json` (DTCG, light + dark, same values as §1–§4).
