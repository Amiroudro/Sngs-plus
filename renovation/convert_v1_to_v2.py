#!/usr/bin/env python3
"""Convert renovated editions v1 -> learning-module v2.

Rules: renovation/CONVERSION_RULES_V2.md
Input : renovated-editions/data-YYYY-MM-DD.json (16 files, 1-16 Nov 2026)
Output: same files, converted in place (v1 backup in
        renovated-editions-v1-backup-2026-11-18/).
Also updates renovated-editions/index.json renovation fields.
Does NOT touch editions/, app/, bn-*.json, Edition 11.

Usage: python3 renovation/convert_v1_to_v2.py [--overrides FILE]
Writes: renovation/conversion-log.jsonl (one line per exam_notes point)
        renovation/conversion-ns-log.json
        renovation/conversion-summary.json
"""
import json, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RENO = BASE / "renovated-editions"
MARKER = "যাচাই করা যায়নি — ফাঁকা রাখা হয়েছে"
BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

ORG_WORDS = ["মন্ত্রণালয়","কমিশন","বোর্ড","ব্যাংক","সংস্থা","ফেডারেশন",
    "অ্যাসোসিয়েশন","কর্তৃপক্ষ","বিভাগ","আদালত","ট্রাইব্যুনাল","বিশ্ববিদ্যালয়",
    "পরিষদ","ইনস্টিটিউট","কাউন্সিল","সংসদ","দপ্তর","অধিদপ্তর","অধিদফতর",
    "গ্রুপ","সচিবালয়","কোম্পানি","কর্পোরেশন","ব্যুরো","এজেন্সি","ফাউন্ডেশন",
    "চেম্বার","সমিতি","ইউনিয়ন","সরকার","মন্ত্রিসভা","কমিটি","সেল","ইউনিট",
    "পিএলসি","লিমিটেড","ট্রাস্ট","কেন্দ্র","মিশন","দূতাবাস","হাইকমিশন",
    "সার্ভিস","বাহিনী","এক্সচেঞ্জ",
    "Bank","Commission","Board","Ministry","Authority","Council","Institute",
    "University","Corporation","Company","Group","Fund","Agency","Court",
    "Tribunal","Department","Division","Federation","Association",
    "Organization","Organisation","Chamber","Mission","Embassy","Parliament",
    "Secretariat","Bureau","Exchange","Service","Force"]
ROLE_WORDS = ["দায়িত্ব","ভূমিকা","কাজ","গঠন","গঠিত","নিয়ন্ত্রক","তদারকি","পরিচালনা",
    "শীর্ষ","সংগঠন","প্রতিষ্ঠা","প্রতিষ্ঠিত","সদস্য","জারি","নির্ধারণ","তত্ত্বাবধান",
    "বাস্তবায়ন","সেবা","সুরক্ষা","নিয়ন্ত্রণ","অর্থায়ন","সহায়তা","কার্যকর",
    "অধীন","পরিচালক","সভাপতি","সম্পাদক","প্রধান","নজরদারি"]
CONCEPT_WORDS = ["নীতি","হার","সূচক","তহবিল","চুক্তি","আইন","ধারা","পদ্ধতি",
    "ব্যবস্থা","কাঠামো","মডেল","প্রক্রিয়া","কর","শুল্ক","ভর্তুকি","ঋণ","রিজার্ভ",
    "মুদ্রানীতি","বাজেট","পরিকল্পনা","কৌশল","সমীক্ষা","জরিপ","প্রতিবেদন",
    "স্কোর","রেটিং","কর্মসূচি","প্রকল্প","উদ্যোগ","সংস্কার","বিধি","অধ্যাদেশ",
    "প্রটোকল","সনদ","ঘোষণা","দলিল","শর্ত","মান","স্তর","ধাপ","পর্ব","অধ্যায়",
    "শ্রেণি","প্রকার","ধরন","নিয়ম","বিধান","অনুদান","বিনিয়োগ","মূলধন",
    "সুদ","মুদ্রাস্ফীতি","মূল্যস্ফীতি","বাণিজ্য","রপ্তানি","আমদানি",
    "দর","আদেশ","নিয়ন্ত্রণ","সংবিধি","সংবিধান","অনুচ্ছেদ","সংশোধনী","টিকা",
    "পরীক্ষা","নির্বাচন","দুর্ভিক্ষ","অভ্যুত্থান","করিডর","অর্থায়ন","অন্তর্ভুক্তি",
    "কংগ্রেস","ইনিশিয়েটিভ","বিমানবন্দর"]
VERB_GUARD = ["বাড়লে","কমলে","করেছে","হয়েছে","হচ্ছে","যাচ্ছে","দিয়েছে",
    "নিয়েছে","পেয়েছে","গিয়েছে","এসেছে","করলে","হলে","থাকে","থাকেন","আসে",
    "যায়","করে","হয়","দেয়","নেয়","চলে","চায়","পারে","পড়ে","বেড়ে","কমে",
    "বেড়েছে","কমেছে","গেছে","যাবে","করবে","হবে","দেবে","নেবে","চলবে","আসবে",
    "যাচ্ছেন","করছেন","হচ্ছেন","দিচ্ছেন","নিচ্ছেন","বলেছেন","জানিয়েছেন",
    "পড়েছে","উঠেছে","নেমেছে","দেখে","দেখায়"]
BN_PUB = {"প্রথম আলো (ইংরেজি)":"Prothom Alo English",
    "দ্য বিজনেস স্ট্যান্ডার্ড":"The Business Standard",
    "বিবিসি":"BBC","দ্য ডেইলি স্টার":"The Daily Star",
    "প্রথম আলো":"Prothom Alo","ঢাকা ট্রিবিউন":"Dhaka Tribune"}

def _build_acronyms():
    """Acronyms attested in the corpus: short token before a long
    parenthesised expansion, or a short all-caps parenthesised token."""
    acr = set()
    for path in sorted(RENO.glob("data-*.json")):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(
                r"([\u0985-\u09E5A-Za-z0-9][\u0985-\u09E5A-Za-z0-9 .\-]{0,30}?)"
                r"\s*\(([^)]{1,70})\)", text):
            before, inside = m.group(1).strip(), m.group(2).strip()
            bt = before.split()
            if len(inside) <= 10 and re.fullmatch(
                    r"[A-Z0-9][A-Z0-9 .&\-]*", inside):
                acr.add(inside.split()[0])
            # token before a LONG expansion: NOT used — it also catches
            # ordinary words ("মজুরি" before "(minimum wage ...)"),
            # which then corrupt names ("মজুরি বোর্ড" -> "মজুরি").
            # Bangla acronyms are covered by the manual set below.
            # Bangla token before a short LATIN-caps paren:
            # "ডিজিএইচএস (DGHS)", "স্রেডা (SREDA)"
            if bt and len(bt[-1]) <= 8 and re.fullmatch(
                    r"[\u0985-\u09E5]{2,8}", bt[-1]) and re.fullmatch(
                    r"[A-Z][A-Z0-9&.\-]{1,}", inside):
                acr.add(bt[-1])
    # bodies seen as bare leading tokens (never parenthesised in corpus)
    acr |= {"দুদক", "ইইউ", "ডিজিএইচএস", "ইপিবি", "বিইআরসি", "বিপিএসসি",
            "এনসিটিবি", "স্রেডা", "ইউজিসি", "রাজউক", "এনইসি", "ডাইফ",
            "এনবিআর", "বিজিএমইএ", "বিকেএমইএ", "বিবিসি", "বিআরটিসি",
            "ডিএসই", "বিএমইটি", "সিআরসিসি", "ইসি", "বিআইপি", "ডিএসসিসি",
            "এনসিটিবি", "বিআরটিএ", "ডিএপি", "আইএমএফ", "ইআরডি", "সিডিপি",
            "ওইসিডি", "একনেক", "আইএমইডি", "বিবিএস", "বিডা", "আইসিজে",
            "বিপিসি", "বিজিবি", "সিপিডি", "বিআইবিএম", "আইসিবি", "সিআইবি",
            "ঢাবি", "ইউএনইপি", "ইউএনওডিসি", "এসিইউ"}
    return acr

def keyword_type(text):
    """Type ('org'/'concept'/None) of the LAST keyword-bearing token.
    A token counts when it equals or ends with a keyword.
    Parenthesised content is ignored only when it holds no Bangla
    characters: a Latin paren is an English expansion/translation, not
    the head's own type signal (\"বিনিময় হার (Exchange Rate)\" must not
    count as an organisation because of the English word Exchange
    inside the parens). A Bangla paren is a gloss in the head's own
    language and keeps its signal (\"ইআইআরআর (অর্থনৈতিক অভ্যন্তরীণ
    প্রত্যাবর্তন হার)\" still counts as a concept via হার)."""
    text = re.sub(r"\([^)]*\)",
                  lambda m: " " if not re.search(r"[অ-হ]", m.group(0))
                  else m.group(0), text or "")
    found = None
    for tok in re.split(r"\s+", text or ""):
        t = tok.strip("।,;:()[]\"'’‘—–-")
        if not t:
            continue
        for w in ORG_WORDS:
            if t == w or (len(w) >= 3 and t.endswith(w) and
                          len(t) - len(w) >= 2):
                found = "org"
                break
        else:
            for w in CONCEPT_WORDS:
                if t == w or (len(w) >= 3 and t.endswith(w) and
                              len(t) - len(w) >= 2):
                    found = "concept"
                    break
    return found

ACRONYMS = _build_acronyms()

# The hand-listed acronyms are (bar ডিএপি, a plan) all named BODIES, so a
# point headed by one of them is an institution even when its rest is a
# bare fact ("বিপিএসসি: সংবিধানের ১৩৭–১৪১ অনুচ্ছেদ").
MANUAL_BODIES = {"দুদক", "ইইউ", "ডিজিএইচএস", "ইপিবি", "বিইআরসি", "বিপিএসসি",
    "এনসিটিবি", "স্রেডা", "ইউজিসি", "রাজউক", "এনইসি", "ডাইফ",
    "এনবিআর", "বিজিএমইএ", "বিকেএমইএ", "বিবিসি", "বিআরটিসি",
    "ডিএসই", "বিএমইটি", "সিআরসিসি", "ইসি", "বিআইপি", "ডিএসসিসি",
    "এনপিএসবি",
    "বিআরটিএ", "আইএমএফ", "ইআরডি", "সিডিপি", "ওইসিডি", "একনেক",
    "আইএমইডি", "বিবিএস", "বিডা", "আইসিজে", "বিপিসি", "বিজিবি",
    "সিপিডি", "বিআইবিএম", "আইসিবি", "সিআইবি", "ঢাবি", "ইউএনইপি",
    "ইউএনওডিসি", "এসিইউ"}

# The same bodies in Latin script: exam_notes points often head with the
# Latin acronym ("NBR = National Board of Revenue ..."), which the "="
# and acronym branches must also recognise as a body, not a term.
# Plus Latin-only bodies found in the corpus audit (UNHCR, UNEP,
# UNFCCC, BOESL, IDA, DTCA, PPPA, BAKSAL, GCF, EDCF).
LATIN_BODIES = {"ACC", "ACU", "BAKSAL", "BB", "BBS", "BERC", "BGMEA",
    "BIBM", "BIDA", "BIP", "BKMEA", "BMET", "BOESL", "BPATC", "BPSC",
    "BRTA", "BRTC", "BTRC", "BGB", "BBC", "CDP", "CIB", "CPD", "DIFE",
    "DGHS", "DSCC", "DSE", "DTCA", "EC", "ECNEC", "EDCF", "EPB",
    "ERD", "GCF", "ICB", "ICJ", "IDA", "IMED", "IMF", "NBR", "NCTB",
    "NEC", "NPSB", "OECD", "PPPA", "RAJUK", "SREDA", "UGC", "UNEP",
    "UNFCCC", "UNHCR", "UNODC"}

def has_role_word(text):
    return any(w in text for w in ROLE_WORDS)

def split_head_rest(point):
    """Return (head, rest) for 'Head: rest' or 'Head — rest'."""
    m = re.match(r"^\s*(.+?)\s*[:：]\s+(.*)$", point, re.S)
    if m and len(m.group(1).strip()) <= 120:
        return m.group(1).strip(), m.group(2).strip()
    m = re.match(r"^\s*(.+?)\s+[—–]\s+(.*)$", point, re.S)
    if m and len(m.group(1).strip()) <= 120:
        return m.group(1).strip(), m.group(2).strip()
    return None, None

def _is_expansion(paren):
    """Is a parenthesised bit an expansion/gloss (vs a year/note)?"""
    p = paren.strip()
    if not p or p[0].isdigit() or "০" <= p[0] <= "৯":
        return False
    # a citation qualifier ("কলাম অনুযায়ী") is not an expansion
    if any(w in p for w in ("অনুযায়ী", "অনুসারে", "মতে")):
        return False
    if re.fullmatch(r"[A-Z][A-Z0-9&.\-]{1,}", p):
        return True
    return " " in p

def parse_name(head):
    """'NAME (Expansion)' -> (name, full_name or None).
    A parenthesised year/note stays attached to the name."""
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", head)
    if m and _is_expansion(m.group(2)):
        return m.group(1).strip(), m.group(2).strip()
    return head.strip(), None

def is_acronym_token(tok):
    t = tok.strip("।,;:()[]\"'’‘")
    if t in ACRONYMS:
        return True
    return bool(re.fullmatch(r"[A-Z][A-Z0-9&.\-]{1,}", t))

def _acronym_first_token(head):
    """If head starts with an acronym token + descriptive words, return
    (acronym, rest-of-head); else (None, head)."""
    toks = head.split()
    if len(toks) > 1 and is_acronym_token(toks[0]):
        return toks[0], " ".join(toks[1:])
    return None, head

def classify_point(point):
    """Return (kind, entry-fields-dict, confidence).
    kind in {'institution','term','remainder'}."""
    # A generic field label ("সদর দপ্তর ইনচিওন, ...") or a proposal
    # ("প্রস্তাবিত দুই বিভাগ: ...") is not a body: leave it as a
    # remainder so the continuation logic can attach it to the previous
    # entry (an HQ fragment merges into the body it belongs to) or it
    # stands alone as a factoid.
    _p = point.strip()
    if _p.startswith(("সদর দপ্তর", "প্রধান কার্যালয়", "সদর কার্যালয়")) \
            or _p.startswith(("প্রস্তাবিত ", "পরিকল্পিত ", "সম্ভাব্য ")):
        _head = re.split(r"[—:।;]", _p)[0].strip()
        _term = _head if len(_head) <= 50 else " ".join(_p.split()[:5])
        return "remainder", {"term": _term, "meaning": point}, "low"
    # acronym expansion: "LEAP-এর পূর্ণরূপ: ..."
    m = re.match(r"^\s*(.+?)-এর পূর্ণরূপ\s*[:：]\s*(.*)$", point, re.S)
    if m:
        term = m.group(1).strip()
        rest = m.group(2).strip()
        full = None
        fm = re.match(r"^([A-Za-z][A-Za-z0-9 ,&'’\-]+?)\s*(?:\(|$)", rest)
        if fm and len(fm.group(1).strip()) >= 4:
            full = fm.group(1).strip()
        return "term", {"term": term, "full_name": full,
                        "meaning": point}, "high"
    # "X মানে Y" — term definition
    m = re.match(r"^\s*(.+?)\s+মানে\s+(.*)$", point, re.S)
    if m and len(m.group(1).strip()) <= 45:
        name, full = parse_name(m.group(1).strip())
        return "term", {"term": name, "full_name": full,
                        "meaning": m.group(2).strip()}, "high"
    # "X = Y" — term definition with an equals sign; a KNOWN BODY is an
    # institution instead ("NBR = National Board of Revenue ...").
    m = re.match(r"^\s*(.+?)\s*=\s*(.+)$", point, re.S)
    if m and len(m.group(1).strip()) <= 45:
        name, full = parse_name(m.group(1).strip())
        rest = m.group(2).strip()
        if name in MANUAL_BODIES or name in LATIN_BODIES or \
                (full and full in LATIN_BODIES):
            nm = name if (name in MANUAL_BODIES or
                          name in LATIN_BODIES) else full
            # full name = leading Latin run of the rest, before any
            # dash, paren or Bangla text
            lm = re.match(
                r"^([A-Za-z][A-Za-z0-9 ,&'’\-]*?)(?:\s*[—–]\s*|\s*\(|"
                r"(?=[অ-হ])|$)", rest)
            full_name = lm.group(1).strip() if lm else full
            return "institution", {"name": nm, "full_name": full_name,
                                   "role": rest}, "high"
        rest_clean = rest.rstrip("।").strip()
        if full is None and re.fullmatch(
                r"[A-Za-z][A-Za-z0-9 ,&'’\-()]+", rest_clean) and \
                " " in rest_clean and not any(
                    "অ" <= c <= "হ" for c in rest_clean):
            # the whole rest is a Latin expansion: it is the full name
            return "term", {"term": name, "full_name": rest_clean,
                            "meaning": point}, "high"
        return "term", {"term": name, "full_name": full,
                        "meaning": rest}, "high"
    # section reference anchored at the start: "ধারা ১৩(১) ..." /
    # "শ্রম আইনের ধারা ১৩(১) ..." (text before ধারা must be empty or a
    # short law name containing আইন — never a mid-sentence match)
    m = re.match(r"^\s*((?:[^\s:;]{1,25}\s+){0,4}?"
                 r"(?:আইনের\s+)?ধারা\s*[০-৯0-9]+(?:\([^)]*\))?)"
                 r"\s*(অনুযায়ী|অনুসারে)?\s*(.*)$", point, re.S)
    if m and len(m.group(1).strip()) <= 45 and \
            (m.group(1).strip().startswith("ধারা") or
             "আইন" in m.group(1)):
        return "term", {"term": m.group(1).strip(), "full_name": None,
                        "meaning": point}, "high"
    head, rest = split_head_rest(point)
    if head is not None:
        name, full = parse_name(head)
        acr, head_rest = _acronym_first_token(name)
        htype = keyword_type(head)
        rtype = keyword_type(rest)
        # a known body acronym as head is an institution even when the
        # rest is a bare fact ("বিপিএসসি: সংবিধানের ১৩৭–১৪১ অনুচ্ছেদ")
        if name in MANUAL_BODIES or name in LATIN_BODIES or \
                (acr and (acr in MANUAL_BODIES or acr in LATIN_BODIES)):
            nm = acr if (acr and (acr in MANUAL_BODIES or
                                  acr in LATIN_BODIES)) else name
            role = rest
            if acr and acr == nm and head_rest:
                role = (head_rest + ": " + rest) if rest else head_rest
            return "institution", {"name": nm, "full_name": full,
                                   "role": role if role else point}, "high"
        if htype == "org":
            # "বিইআরসি জ্বালানি খাতের নিয়ন্ত্রক সংস্থা: ..." -> the
            # acronym is the name, the descriptive words join the role
            if acr:
                role = (head_rest + ": " + rest) if rest else head_rest
                return "institution", {"name": acr, "full_name": full,
                                       "role": role}, "high"
            return "institution", {"name": name, "full_name": full,
                                   "role": rest if rest else point}, "high"
        if is_acronym_token(name) or acr:
            # acronym head: institution only with org/role evidence in
            # the rest (NCQG/GNI are terms, not bodies)
            if rtype == "org" or has_role_word(rest):
                if acr:
                    role = (head_rest + ": " + rest) if rest else head_rest
                    return "institution", {"name": acr, "full_name": full,
                                           "role": role}, "high"
                return "institution", {"name": name, "full_name": full,
                                       "role": rest}, "high"
            return "term", {"term": name, "full_name": full,
                            "meaning": rest if rest else point}, "high"
        if htype == "concept":
            return "term", {"term": name, "full_name": full,
                            "meaning": rest if rest else point}, "high"
        # exam-tip labels ("পরীক্ষায় আসে:", "মনে রাখার সংখ্যা:", ...)
        if head.startswith(("পরীক্ষায়", "মনে রাখ", "উৎস মনে",
                            "রায়ের তারিখ মনে")) or \
                any(s in head for s in ("মনে রাখ", "মুখস্থ রাখ",
                                        "পরীক্ষায় আস")):
            return "term", {"term": name, "full_name": full,
                            "meaning": rest if rest else point}, "medium"
        if len(name) <= 40 and not any(
                t in VERB_GUARD for t in head.split()):
            return "term", {"term": name, "full_name": full,
                            "meaning": rest if rest else point}, "medium"
        return "remainder", {"term": name, "meaning": point}, "low"
    # no colon/dash split: "Name (Expansion) rest..." paren-head
    m = re.match(r"^\s*(.+?)\s*\(([^)]+)\)\s+(.*)$", point, re.S)
    if m and len(m.group(1).strip()) <= 40:
        name, full = parse_name(m.group(1).strip() + " (" + m.group(2) + ")")
        rest2 = m.group(3).strip()
        if name in MANUAL_BODIES or name in LATIN_BODIES:
            return "institution", {"name": name, "full_name": full,
                                   "role": rest2}, "high"
        htype = keyword_type(m.group(1))
        rtype = keyword_type(rest2)
        if htype == "org" or rtype == "org" or has_role_word(rest2):
            return "institution", {"name": name, "full_name": full,
                                   "role": rest2}, "high"
        if rtype == "concept" or htype == "concept":
            return "term", {"term": name, "full_name": full,
                            "meaning": rest2}, "high"
        return "term", {"term": name, "full_name": full,
                        "meaning": rest2}, "medium"
    # no colon/dash split: point starts with an acronym token
    # ("ডিজিএইচএস স্বাস্থ্য ও পরিবার কল্যাণ মন্ত্রণালয়ের অধীন; ...")
    toks0 = point.split()
    if len(toks0) > 1 and is_acronym_token(toks0[0]):
        rest0 = " ".join(toks0[1:]).strip()
        if toks0[0] in MANUAL_BODIES or toks0[0] in LATIN_BODIES:
            return "institution", {"name": toks0[0], "full_name": None,
                                   "role": rest0}, "high"
        if has_role_word(rest0) or keyword_type(rest0) == "org":
            return "institution", {"name": toks0[0], "full_name": None,
                                   "role": rest0}, "high"
        if keyword_type(rest0) == "concept":
            return "term", {"term": toks0[0], "full_name": None,
                            "meaning": rest0}, "high"
        return "term", {"term": toks0[0], "full_name": None,
                        "meaning": rest0}, "medium"
    # no colon/dash split: leading org/concept phrase + rest (shortest
    # token-prefix ending in a keyword; a verb before the keyword vetoes).
    # A fragment starting with a year/number is not a headed definition.
    toks = point.split()
    if toks and toks[0][0].isdigit():
        toks = []
    for i in range(1, len(toks) + 1):
        cand = " ".join(toks[:i]).strip("।,;:")
        if len(cand) > 50:
            break
        if any(t in VERB_GUARD for t in toks[:i]):
            break
        kt = keyword_type(cand)
        if kt:
            rest_toks = toks[i:]
            # attach a following ", YYYY" year to the head
            if rest_toks and re.fullmatch(
                    r",?[০-৯0-9]{4},?", rest_toks[0]):
                cand = cand + " " + rest_toks[0].strip(",")
                rest_toks = rest_toks[1:]
            rest2 = " ".join(rest_toks).strip()
            if len(rest2) >= 5:
                if kt == "org":
                    return "institution", {"name": cand, "full_name": None,
                                           "role": rest2}, "medium"
                return "term", {"term": cand, "full_name": None,
                                "meaning": rest2}, "medium"
            break
    # no colon split: "X হলো/হচ্ছে ..."
    m = re.match(r"^\s*(.+?)\s+(হলো|হচ্ছে|হল)\s+(.*)$", point, re.S)
    if m and len(m.group(1).strip()) <= 45:
        head, rest = m.group(1).strip(), m.group(3).strip()
        if keyword_type(head) == "org" or is_acronym_token(head):
            return "institution", {"name": head, "full_name": None,
                                   "role": rest}, "medium"
        return "term", {"term": head, "full_name": None,
                        "meaning": rest}, "medium"
    # no structure at all -> remainder; the label is the head before the
    # first break, else the first five words (verbatim), never invented
    head = point
    for sep in ("—", ":", "।", ";"):
        head = head.split(sep)[0]
    head = head.strip()
    if 0 < len(head) <= 50:
        term = head
    else:
        term = " ".join(point.split()[:5])
    return "remainder", {"term": term, "meaning": point}, "low"

def split_compound(point):
    """Split a point naming two institutions joined by ';'."""
    if ";" not in point and "；" not in point:
        return [point]
    parts = [p.strip() for p in re.split(r"[;；]", point) if p.strip()]
    if len(parts) < 2:
        return [point]
    heads = 0
    for p in parts:
        h, _ = split_head_rest(p)
        cand = h or p[:60]
        first = cand.split()[0] if cand.split() else ""
        if keyword_type(cand) == "org" or is_acronym_token(first):
            heads += 1
    return parts if heads >= 2 else [point]

CONTINUATION_STARTERS = {"লক্ষ্য", "উদ্দেশ্য", "ফলে", "এতে", "এর ফলে",
    "তাতে", "এছাড়া", "আরও", "এছাড়াও", "অর্থাৎ", "যেমন", "তবে", "কিন্তু",
    "প্রতিষ্ঠা", "মোট", "এদিকে", "অন্যদিকে", "সেই সঙ্গে", "পাশাপাশি",
    "সদর"}
VERB_ENDINGS = ("ছে", "ছেন", "বে", "বেন", "লো", "লেন", "তেছে", "তেছেন")

def continuation_merge(fragment, last, seen=None):
    """Does this fragment continue the previous entry? last is
    (section_list, entry, key_field). seen is the story's
    name -> entry map. Returns True/False."""
    if last is None or len(fragment) > 120:
        return False
    toks = fragment.split()
    first = toks[0] if toks else ""
    if first in ("এই", "এইসব", "ওই", "ওইসব"):
        return False  # demonstrative + new subject, not a continuation
    if first in ("এর", "এটি", "তার", "তাদের", "সেটি", "সেটা", "এরা"):
        return True
    if "এমন" in fragment:
        return True
    if first in CONTINUATION_STARTERS:
        return True
    # a year in a short fragment almost always continues the previous
    # entry's history ("প্রতিষ্ঠা ১৯৭২", "একীভূত কমিশন ১৯৭৭")
    if len(fragment) <= 60 and re.search(r"[১-২][৯০][০-৯]{2}", fragment):
        return True
    # short verbless fragment ("মোট ১,৭২২ বিশ্ববিদ্যালয়।",
    # "জাতিসংঘের প্রধান বিচারিক সংস্থা")
    if len(fragment) <= 30 and not any(
            t in VERB_GUARD for t in toks) and not any(
            t.endswith(VERB_ENDINGS) for t in toks):
        return True
    entry = last[1]
    name = entry.get("name") or entry.get("term") or ""
    # if the fragment names a DIFFERENT body/term already seen in this
    # story, it belongs to that entry, not to the previous one
    # (e.g. a consulate sentence after a BMET entry: "বিদেশে" also
    # appears in BMET's role, but the sentence is about the consulate).
    # Word-level: a seen name like "পররাষ্ট্র মন্ত্রণালয় ও কনস্যুলেট"
    # is named by any of its distinctive words ("কনস্যুলেট").
    if seen:
        last_words = set(name.split())
        for nm in seen:
            if nm == name:
                continue
            for w in nm.split():
                w = w.strip("।,;:()[]\"'’‘")
                if len(w) >= 4 and w not in last_words and w in fragment:
                    return False
    for w in name.split():
        w = w.strip("।,;:()[]\"'’‘")
        if len(w) >= 4 and w in fragment:
            return True
    body = entry.get(last[2], "") or ""
    fw = first.strip("েতেরকেয়ও।,")
    if len(fw) >= 3 and fw in body:
        return True
    return False

def merge_into(entry, key, fragment):
    """Append a continuation fragment to an entry's role/meaning,
    separating with '। ' when the existing text has no terminal
    punctuation (the '।' is a separator between verbatim fragments,
    not new content)."""
    cur = entry.get(key) or ""
    sep = " " if cur.rstrip().endswith(("।", ".", ";", ":", "!", "?")) \
        else "। "
    entry[key] = cur + sep + fragment

def merge_dup(existing, key, new_text, new_full=None):
    """Merge a same-name entry's text into the existing entry instead of
    dropping it (a re-mention usually adds new content, e.g. a pre-split
    institution restated in the notes with extra detail). If the new
    text already contains the old one, the new text replaces it."""
    cur = existing.get(key) or ""
    if new_text and new_text not in cur:
        if cur and cur in new_text:
            existing[key] = new_text
        else:
            merge_into(existing, key, new_text)
    if new_full and "full_name" not in existing:
        rebuilt = {}
        for k, v in existing.items():
            rebuilt[k] = v
            if k in ("name", "term"):
                rebuilt["full_name"] = new_full
        existing.clear()
        existing.update(rebuilt)

def make_source_str(sources):
    return "; ".join(s["name"] for s in sources)

def norm_date(d):
    """Bangla-digit YYYY-MM-DD -> Latin ISO (same date, other script)."""
    if isinstance(d, str) and re.fullmatch(r"[০-৯]{4}-[০-৯]{2}-[০-৯]{2}", d):
        return d.translate(BN_DIGITS)
    return d

def convert_news_summary(lm, story, edition_date, log):
    ns = lm["news_summary"]
    text, src = None, None
    rule = None
    if isinstance(ns, dict) and isinstance(ns.get("source"), dict):
        text = ns["text"]
        src = {"publication": ns["source"]["publication"],
               "date": norm_date(ns["source"]["date"]),
               "url": ns["source"]["url"]}
        rule = "already-object"
    elif isinstance(ns, dict) and isinstance(ns.get("source_line"), str):
        text = ns["text"]
        line = ns["source_line"]
        url = None
        m = re.search(r"https?://\S+", line)
        if m:
            url = m.group(0).rstrip(".,)")
        match = next((s for s in story["sources"]
                      if s.get("url") == url), None)
        assert match, f"source_line URL not in story sources: {story['id']}"
        src = {"publication": match["publication"], "date": match["date"],
               "url": match["url"]}
        rule = "source_line-url-match"
    elif isinstance(ns, dict) and isinstance(ns.get("source"), str):
        text = ns["text"]
        sstr = ns["source"]
        pub_bn = sstr.split(",")[0].strip()
        pub_en = BN_PUB.get(pub_bn)
        match = None
        for s in story["sources"]:
            if pub_en and s.get("publication") == pub_en:
                match = s
                break
        if match is None:
            match = story["sources"][0]
            rule = "source-string-fallback-first"
        else:
            rule = "source-string-name-match"
        src = {"publication": match["publication"], "date": match["date"],
               "url": match["url"]}
    elif isinstance(ns, str):
        text = ns
        s0 = story["sources"][0]
        src = {"publication": s0["publication"], "date": s0["date"],
               "url": s0["url"]}
        rule = "plain-string-first-source"
    else:
        raise ValueError(f"unknown news_summary shape: {story['id']} {ns!r:.80}")
    log.append({"edition": edition_date, "story": story["id"], "rule": rule,
                "publication": src["publication"]})
    return {"text": text, "source": src}

def convert_mcq(m):
    opts = m["options"]
    assert set(opts) == set("ABCD"), f"mcq options not A-D: {m}"
    assert m["correct"] in "ABCD", f"mcq correct bad: {m}"
    assert m.get("explanation"), f"mcq missing explanation: {m}"
    out = {"question": m["question"],
           "options": [opts["A"], opts["B"], opts["C"], opts["D"]],
           "correct": "ABCD".index(m["correct"]),
           "explanation": m["explanation"]}
    if "no" in m:
        out["no"] = m["no"]
    return out

def convert_written(w, sid):
    if isinstance(w, dict) and "short_question" in w:
        return {"short": {"question": w["short_question"],
                          "outline": w["short_outline"]},
                "analytical": {"question": w["analytical_question"],
                               "outline": w["analytical_outline"]}}
    if isinstance(w, dict) and "short" in w and "analytical" in w:
        return {"short": {"question": w["short"]["question"],
                          "outline": w["short"]["outline"]},
                "analytical": {"question": w["analytical"]["question"],
                               "outline": w["analytical"]["outline"]}}
    if isinstance(w, list) and len(w) == 2:
        short = analytical = None
        for it in w:
            outline = it.get("outline") or it.get("model_outline") or \
                      it.get("model_answer_outline")
            assert outline, f"written_prep item without outline: {sid}"
            q = it["question"]
            t = (it.get("type") or "").strip()
            if t in ("সংক্ষিপ্ত প্রশ্ন", "সংক্ষিপ্ত", "short"):
                short = {"question": q, "outline": outline}
            elif t in ("বিশ্লেষণধর্মী প্রশ্ন", "বিশ্লেষণধর্মী", "analytical"):
                analytical = {"question": q, "outline": outline}
            elif "সংক্ষিপ্ত" in q or "সংক্ষেপে" in q:
                short = {"question": q, "outline": outline}
            elif "বিশ্লেষণ" in q:
                analytical = {"question": q, "outline": outline}
            elif short is None:
                short = {"question": q, "outline": outline}
            else:
                analytical = {"question": q, "outline": outline}
        assert short and analytical, f"written_prep unresolved: {sid}"
        return {"short": short, "analytical": analytical}
    raise ValueError(f"unknown written_prep shape: {sid} {str(w)[:120]}")

def split_list_str(val):
    parts = []
    for p in val.split(";"):
        parts.extend(p.split(","))
    return [p.strip() for p in parts if p.strip()]

def convert_vocab(v):
    return {"word": v["word"], "meaning_bn": v["bangla_meaning"],
            "example": v["example"],
            "synonyms": split_list_str(v["synonym"]),
            "antonyms": split_list_str(v["antonym"])}

def convert_revision(r):
    fcs = []
    for fc in r["flashcards"]:
        if "q" in fc:
            fcs.append({"q": fc["q"], "a": fc["a"]})
        else:
            fcs.append({"q": fc["question"], "a": fc["answer"]})
    return {"flashcards": fcs, "next_revision": r["next_revision"]}

def convert_story(story, edition_date, log_lines, ns_log, overrides):
    lm = story["learning_module"]
    sid = story["id"]
    key = f"{edition_date}|{sid}"
    en = lm["exam_notes"]
    src_str = make_source_str(en["sources"]) if isinstance(en, dict) else ""
    # --- institutions / extra_knowledge ---
    if isinstance(en, str):
        assert en == MARKER, f"unexpected marker: {sid} {en!r}"
        institutions, extra = MARKER, MARKER
    else:
        institutions, extra = [], []
        seen = {}  # display name -> (list, entry, key_field, kind)

        def _name_keys(nm):
            """Dedup keys for a name: itself, plus — when it ends in a
            parenthesised acronym — the base name and the bare acronym,
            so \"গ্রিন ক্লাইমেট ফান্ড (GCF)\" and a later bare \"GCF\"
            merge into one entry instead of listing the same body
            twice."""
            keys = {nm}
            m = re.match(r"^(.*?)\s*\(([A-Za-z]{2,})\)\s*$", nm)
            if m:
                keys.add(m.group(1).strip())
                keys.add(m.group(2))
            return keys

        def add_entry(entry, key_field, kind):
            """Append entry to its section, MERGING into an existing
            same-name entry instead of dropping new content. A term that
            turns out to be a body is promoted to institutions. Returns
            the (list, entry, key) triple for the merge anchor."""
            name = entry.get("name") or entry.get("term")
            tgt = institutions if kind == "institution" else extra
            for k in _name_keys(name):
                if k in seen:
                    elist, eentry, ekey, ekind = seen[k]
                    if kind == "institution" and ekind == "term":
                        extra.remove(eentry)
                        for kk in _name_keys(eentry.get("name") or
                                             eentry.get("term")):
                            seen.pop(kk, None)
                        new = {"name": name}
                        full = entry.get("full_name") or \
                            eentry.get("full_name")
                        if full:
                            new["full_name"] = full
                        new["role"] = eentry["meaning"]
                        new["source"] = entry["source"]
                        merge_dup(new, "role", entry.get(key_field))
                        institutions.append(new)
                        for kk in _name_keys(name):
                            seen[kk] = (institutions, new, "role",
                                        "institution")
                        log_lines[-1]["dedup-merge"] = "promoted"
                        return institutions, new, "role"
                    merge_dup(eentry, ekey, entry.get(key_field),
                              entry.get("full_name"))
                    log_lines[-1]["dedup-merge"] = (
                        "cross-section" if ekind != kind else
                        ("same-name" if k == name else "alias"))
                    return elist, eentry, ekey
            tgt.append(entry)
            for k in _name_keys(name):
                seen[k] = (tgt, entry, key_field, kind)
            return tgt, entry, key_field
        last = None  # (section_list, entry, key_field) for merge anchor
        # pre-split institutions first
        for it in en.get("institutions", []):
            if isinstance(it, dict):
                entry = {"name": it["name"], "role": it["role"]}
                if it.get("full_name"):
                    entry = {"name": it["name"],
                             "full_name": it["full_name"],
                             "role": it["role"]}
                entry["source"] = src_str
                log_lines.append({"edition": edition_date, "story": sid,
                    "field": "institutions(pre-split)", "point": it,
                    "kind": "institution", "confidence": "pre-split",
                    "entry": entry})
            else:
                head, rest = split_head_rest(it)
                name, full = parse_name(head) if head else (it, None)
                entry = {"name": name}
                if full:
                    entry["full_name"] = full
                entry["role"] = rest if rest else it
                entry["source"] = src_str
                log_lines.append({"edition": edition_date, "story": sid,
                    "field": "institutions(pre-split)", "point": it,
                    "kind": "institution", "confidence": "pre-split",
                    "entry": entry})
            last = add_entry(entry, "role", "institution")
        # notes / points / key_points
        points = []
        for field in ("points", "notes", "key_points"):
            for idx, p in enumerate(en.get(field, [])):
                points.append((field, idx, p))
        for field, idx, p in points:
            okey = f"{key}|{field}|{idx}"
            for j, seg in enumerate(split_compound(p)):
                ov = overrides.get(f"{okey}|seg{j}") or overrides.get(okey)
                if ov:
                    kind = ov["kind"]
                    fields = {k: v for k, v in ov.items()
                              if k != "kind" and v is not None}
                    fields["source"] = src_str
                    conf = "override"
                else:
                    kind, fields, conf = classify_point(seg)
                    fields = dict(fields)
                    fields["source"] = src_str
                # drop None full_name
                fields = {k: v for k, v in fields.items() if v is not None}
                if kind == "merge":
                    # override: append this fragment to the previous entry
                    tgt_list, tgt_entry, tgt_key = last
                    merge_into(tgt_entry, tgt_key, seg)
                    log_lines.append({"edition": edition_date, "story": sid,
                        "field": field, "point": seg, "kind": "merged",
                        "confidence": "override",
                        "entry": {"into": tgt_entry.get("name") or
                                  tgt_entry.get("term"),
                                  "field": tgt_key}})
                    continue
                if kind == "remainder" and conf != "override" and \
                        continuation_merge(seg, last, seen):
                    tgt_list, tgt_entry, tgt_key = last
                    merge_into(tgt_entry, tgt_key, seg)
                    log_lines.append({"edition": edition_date, "story": sid,
                        "field": field, "point": seg, "kind": "merged",
                        "confidence": "continuation",
                        "entry": {"into": tgt_entry.get("name") or
                                  tgt_entry.get("term"),
                                  "field": tgt_key}})
                    continue
                log_lines.append({"edition": edition_date, "story": sid,
                    "field": field, "point": seg, "kind": kind,
                    "confidence": conf, "entry": fields})
                if kind == "institution":
                    last = add_entry(fields, "role", "institution")
                else:
                    last = add_entry(fields, "meaning", "term")
        # framing 'text' paragraph -> first extra_knowledge entry
        if en.get("text"):
            entry = {"term": "পরীক্ষার জন্য মনে রাখুন",
                     "meaning": en["text"], "source": src_str}
            extra.insert(0, entry)
            log_lines.append({"edition": edition_date, "story": sid,
                "field": "text", "point": en["text"],
                "kind": "term", "confidence": "fixed-label",
                "entry": entry})
    # --- assemble new learning_module (key order per v2 model) ---
    new_lm = {
        "hero": lm["hero"],
        "news_summary": convert_news_summary(lm, story, edition_date, ns_log),
        "verified_facts": lm["verified_facts"],
        "topic_gk": lm["topic_gk"],
        "institutions": institutions,
        "extra_knowledge": extra,
        "mcq_practice": [convert_mcq(m) for m in lm["mcq_practice"]],
        "written_prep": convert_written(lm["written_prep"], sid),
        "vocabulary": [convert_vocab(v) for v in lm["vocabulary"]],
        "revision": convert_revision(lm["revision"]),
        "deep_prep": lm["deep_prep"],
    }
    assert "exam_notes" not in new_lm
    assert len(new_lm["mcq_practice"]) == 4
    assert len(new_lm["vocabulary"]) == 5
    assert 3 <= len(new_lm["revision"]["flashcards"]) <= 5
    assert len(new_lm["revision"]["next_revision"]) == 2
    assert 4 <= len(new_lm["deep_prep"]) <= 6
    return new_lm

def main():
    overrides = {}
    if "--overrides" in sys.argv:
        i = sys.argv.index("--overrides")
        overrides = json.loads(Path(sys.argv[i + 1]).read_text(encoding="utf-8"))
    log_lines = []
    ns_log = []
    summary = {"editions": {}, "stories": 0, "kinds": {},
               "confidences": {}, "remainders": [], "merged": 0}
    for path in sorted(RENO.glob("data-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        ed = data["edition_date"]
        n = 0
        for story in data["stories"]:
            assert "learning_module" in story, f"{ed} {story['id']} no LM"
            story["learning_module"] = convert_story(
                story, ed, log_lines, ns_log, overrides)
            n += 1
        data["renovation_format"] = "learning-module-v2"
        data["renovation_date"] = "2026-11-18"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                        encoding="utf-8")
        summary["editions"][ed] = n
        summary["stories"] += n
    # index.json renovation fields
    idx_path = RENO / "index.json"
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    for e in idx["editions"]:
        if "renovation_format" in e:
            e["renovation_format"] = "learning-module-v2"
            e["renovation_date"] = "2026-11-18"
    rs = idx.get("renovation_summary", {})
    rs["format"] = "learning-module-v2"
    rs["date"] = "2026-11-18"
    rs["note"] = ("Each story carries a learning_module in the 11-section "
        "v2 format (hero + news summary + verified facts + topic GK + "
        "institutions + extra knowledge + MCQ practice + written prep + "
        "vocabulary + revision + deep prep). News facts and GK facts are in "
        "separate sections with separate sources; exam_notes is dropped, "
        "its content split into institutions and extra knowledge.")
    idx["renovation_summary"] = rs
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    for line in log_lines:
        summary["kinds"][line["kind"]] = summary["kinds"].get(line["kind"], 0) + 1
        summary["confidences"][line["confidence"]] = \
            summary["confidences"].get(line["confidence"], 0) + 1
        if line["kind"] == "remainder":
            summary["remainders"].append(
                {"edition": line["edition"], "story": line["story"],
                 "point": line["point"]})
        if line["kind"] == "merged":
            summary["merged"] += 1
        if "dedup-merge" in line:
            summary["dedup_merges"] = summary.get("dedup_merges", 0) + 1
            summary.setdefault("dedup_merge_kinds", {})
            summary["dedup_merge_kinds"][line["dedup-merge"]] = \
                summary["dedup_merge_kinds"].get(line["dedup-merge"], 0) + 1
    (BASE / "renovation" / "conversion-log.jsonl").write_text(
        "".join(json.dumps(l, ensure_ascii=False) + "\n" for l in log_lines),
        encoding="utf-8")
    (BASE / "renovation" / "conversion-ns-log.json").write_text(
        json.dumps(ns_log, ensure_ascii=False, indent=1), encoding="utf-8")
    (BASE / "renovation" / "conversion-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
