# PREVIEW BRIEF — Sarangsho Plus app v2 (for the web preview)

The Flutter app was rebuilt to a premium standard (v1.1.0+2). This brief
lets the web preview match it exactly. Colours, type, spacing, motion
and features below are the FINAL decisions — do not reuse v1 tokens.

## 1. Final palette — ONE accent (changed in v2)

Rudro freed the palette; the old orange-red is RETIRED from the UI.
Single-accent emerald editorial palette:

| Token | Value | Use |
|---|---|---|
| Emerald (primary) | `#0B5D3B` | Primary buttons, selected nav, section headings, links, bookmarks, progress, score ring |
| Emerald dark | `#073D27` | Gradient end (hero/header), dark accents |
| Emerald light (dark mode accent) | `#6FC79B` | Primary/accent text on dark surfaces |
| Emerald mid | `#4CAF7D` | Dark-mode secondary |
| Emerald tint | `#E6F1EB` | Light tint fills (chips, icon circles, selected states) |
| Paper (light bg) | `#FAF8F3` | App background |
| Surface (light) | `#FFFFFF` | Cards |
| Soft surface | `#F3EFE6` | Layered surface / skeleton |
| Ink | `#1B1A17` | Primary text |
| Ink secondary | `#6B655E` | Secondary text |
| Ink faint | `#98928A` | Captions / hints |
| Hairline | `#E7E1D6` | 1px borders |
| Amber (system warning only) | `#9A6A12` | "Medium" relevance |
| Error (system only) | `#B3261E` | Wrong answers |

Dark mode: paper `#131311`, surface `#1E1E1B`, soft `#2A2A26`,
ink `#F2EFE9` (off-white), secondary `#B8B2A8`, faint `#8A857C`,
hairline `#33332E`, emerald tint `#173325`. Depth via lighter
surfaces, never inverted colours.

Why emerald: calm, editorial, trustworthy with Bengali text; AAA
contrast on warm paper; continuity with the green brand/icon (the
launcher icon is now emerald-only — white "সা" on `#0B5D3B`, no orange
bar). App bars are quiet paper surfaces with ink titles; colour lives
in the Home hero and primary buttons only.

## 2. Typography (one scale, every screen)

- Display (app name): 32, w900, 1.1, letter-spacing −0.5
- Title: 22, w800, 1.25
- Headline: 20, w800, 1.3
- Section: 17, w800, 1.35
- Body: 16, 1.6 (Bengali body line height 1.6; minimum body 14)
- Body small: 14, 1.6
- Caption: 12, 1.4
- Label/chip: 13, w700
- Hierarchy by weight + colour, not size alone. Bengali-first; only
  English word headwords stay English.

## 3. Spacing / shape / depth

- 8pt grid: 4 / 8 / 12 / 16 / 24 / 32 / 48. Screen padding 16.
  Section gap 24. Card padding 16.
- Radii: card 20, bottom sheet 28 (top), button 14, chip pill, small 10.
- Cards: white/dark-lifted surface, 1px hairline border, soft diffused
  shadow (blur 16, offset y4, black 6%). Lifted shadow (blur 28, y10,
  8%) for the hero cover only.
- Touch targets 48dp minimum. One primary action per screen.

## 4. Motion — ONE language everywhere

- Curve: cubic-bezier(0.16, 1, 0.3, 1) — slow, soft, deliberate.
- Durations: 180ms fast, 320ms standard, 360ms page transitions.
- Page transition: fade + 3% upward slide, same curve.
- Staggered list entry: fade + 12px rise, 45ms per item (max 8).
- Hero transition on story open (headline flies from card to detail).
- Word expand: smooth height animation + chevron rotates 180°.
- Flashcard flip: 3D rotateY with perspective.
- Quiz result: score ring counts up over 900ms.
- Skeleton screens (pulsing blocks) while loading — never spinners.

## 5. Home — the striking first screen

- Emerald gradient hero (emerald → emerald dark) with a giant faint
  "সা" watermark (7% white, bottom-right).
- Greeting (small), wordmark "সারাংশ প্লাস" 32 w900 white, full date
  ("শনিবার, ৮ নভেম্বর ২০২৬"), offline pill ("অফলাইন • ডাউনলোড করা").
- Edition switcher (translucent white), white pill search bar,
  stats strip (3 numbers: খবর / শব্দ / প্রশ্ন, hairline dividers),
  English + Quiz white action cards.
- Top story as a full-bleed emerald COVER card ("প্রধান খবর" pill,
  headline 22 white, 3-line summary, source names + arrow).
- Section chips (emerald tint when selected), story list below.
- Pull-to-refresh on Home.

## 6. Screens

- **Story detail:** emerald cover header with hero headline; reading
  progress bar (emerald, 3px) under the app bar; sections with emerald
  headings; sources in a bottom sheet ("সব সূত্র দেখুন (n)"); bottom
  bar: Share (filled) + Bookmark (outlined).
- **Share:** preview dialog shows the exact image card (emerald band
  with wordmark + date, headline, short summary, relevance + source),
  then shares it as a PNG via the system share sheet (text fallback).
- **Words:** COLLAPSED list — one compact row per word (English
  headword 18 emerald + Bengali meaning + part of speech + chevron).
  Tap expands inline to the full 11-item exam card; one open at a
  time; "পুরো পাতা" button opens the full-page view. Flashcards button
  in the header.
- **Flashcards:** flip deck (front: headword + IPA; back: Bengali
  meaning + synonyms + example), progress bar, "জানি / জানি না"
  buttons, end screen with the honest count.
- **Quiz:** mode cards with soft icon circles; options as tappable
  rows (emerald border + tint when selected); result = animated
  score ring (180px, counts up) + one verdict word
  ("দারুণ!" / "ভালো!" / "চেষ্টা চালিয়ে যান") + Retake / Done + review.
- **Search:** recent searches (persisted, max 8) as chips with a clear
  button; matches highlighted in emerald bold in result headlines.
- **Timeline:** quiet rail — emerald dot per event, hairline line,
  newest first.
- **Library:** 4 tabs; empty states = soft-circle icon + one short line.
- **Profile:** emerald "সা" avatar; settings (language, dark mode,
  FONT SIZE: ছোট / সাধারণ / বড় / খুব বড়); quiz streak card (flame
  icon, streak days, best / average / total, last 5 results);
  7-day tracker; editions card (each edition + "ডাউনলোড করা" pill +
  offline note); GK + About, one line each.
- **Settings:** font-size setting persists (0.9 / 1.0 / 1.15 / 1.3,
  multiplies the system text size).

## 7. Copy rule

No filler text anywhere. Short labels only; empty states are one line;
explanations were cut (see test report for the cut list). Story
content, word data and quiz explanations are real data, untouched.

## 8. APK (v2, চূড়ান্ত — ২০২৬-১১-০৮ ০১:৩০ Asia/Dhaka)

- Version 1.1.0+2, package com.sarangsho.plus
- arm64-v8a APK: **17.5 MB** (17,457,750 bytes, SHA-1 `8b9ee5cff1b5bf737207f2c39aaed08be31b8a67`) — headline, most modern phones
- armeabi-v7a APK: 14.9 MB (14,904,628 bytes)
- x86_64 APK: 18.6 MB (18,630,005 bytes)
- Fat APK: 49.0 MB (48,973,639 bytes; v1 was 48.1 MB — fat slightly larger, per-ABI install is what matters: 48.1 → 17.5 MB, −64%)
- Built with --split-per-abi + R8 minify + resource shrinking.
- No new dependencies (share is a minimal native method channel).
- Size breakdown (arm64): lib/arm64-v8a 16 MB (Flutter engine + Dart AOT; our code 225 KB), flutter_assets 148 KB, classes.dex 445 KB.
