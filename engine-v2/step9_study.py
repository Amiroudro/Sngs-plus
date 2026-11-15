#!/usr/bin/env python3
"""Step 9 — Study features / SRS state (Sarangsho Plus engine v2).

The engine only produces and updates SRS state as JSON; the app
renders the quiz UI from this state.

Intervals (RULES.md Step 9 / CONTRACTS.md): a correct answer moves
the card to the next interval in 1, 3, 7, 14 days by repetitions
(1st correct -> +1 day, then +3, +7, +14). A wrong answer resets
repetitions to 0 and brings the card back tomorrow (+1 day).
A reported card (\"ভুল রিপোর্ট করুন\") is removed from the quiz
until review: reported = true, next_review = null.

All Step 5 checks must have passed before a fact enters the quiz:
``build_cards`` accepts only questions carrying ``"checked": true``
(Step 8 sets this flag when the source quote passes the verbatim
check) and skips everything else.

``quiz_due`` returns yesterday's facts first: due cards sorted by
next_review, oldest first.

Stdlib-only Python 3. No publishing, no LLM.
"""
from datetime import date as _date, timedelta

# SRS intervals in days, by repetitions after a correct answer:
# 1st correct -> 1, 2nd -> 3, 3rd -> 7, 4th and later -> 14.
INTERVALS = (1, 3, 7, 14)


def _as_date(value):
    """Accept a 'YYYY-MM-DD' string or a datetime.date; return a date."""
    if isinstance(value, _date):
        return value
    return _date.fromisoformat(str(value).strip()[:10])


def _add_days(day, days):
    return _as_date(day) + timedelta(days=days)


def _iso(day):
    return _as_date(day).isoformat()


def _flatten_questions(questions):
    """Accept a flat list of question dicts, or bundles such as
    {"qa": [...], "mcq": [...]} as returned by Step 8."""
    flat = []
    for q in questions or []:
        if isinstance(q, dict) and ("qa" in q or "mcq" in q):
            flat.extend(q.get("qa") or [])
            flat.extend(q.get("mcq") or [])
        else:
            flat.append(q)
    return flat


def build_cards(questions, date):
    """Build the SRS state for ``date`` from Step 8 questions.

    Only questions with ``"checked": true`` become cards — that flag
    means all Step 5 checks passed for the underlying fact (Step 8
    sets it when the source quote is verified verbatim). Anything
    unchecked, or missing an id / question text, is skipped.

    Each new card: next_review = tomorrow, interval_days = 1,
    repetitions = 0, reported = false.
    """
    cards = []
    for q in _flatten_questions(questions):
        if not isinstance(q, dict):
            continue
        if q.get("checked") is not True:
            continue  # Step 5 checks not passed: never enters the quiz.
        question_id = q.get("question_id") or q.get("id")
        text = q.get("question") or q.get("stem")
        if not question_id or not text:
            continue
        cards.append({
            "fact_id": q.get("fact_id") or f"{question_id}-fact",
            "question_id": question_id,
            "question": text,
            "next_review": _iso(_add_days(date, 1)),
            "interval_days": 1,
            "repetitions": 0,
            "reported": False,
        })
    return {"date": _iso(date), "cards": cards}


def grade_answer(card, correct, today):
    """Return an updated copy of ``card`` after an answer on ``today``.

    Correct: repetitions + 1, interval follows 1, 3, 7, 14 by
    repetitions (1st correct +1 day, then +3, +7, +14).
    Wrong: repetitions reset to 0, next_review = today + 1 day.
    A reported card is not graded (returned unchanged).
    """
    updated = dict(card)
    if updated.get("reported"):
        return updated
    if correct:
        reps = int(updated.get("repetitions", 0)) + 1
        interval = INTERVALS[min(reps - 1, len(INTERVALS) - 1)]
        updated["repetitions"] = reps
        updated["interval_days"] = interval
        updated["next_review"] = _iso(_add_days(today, interval))
    else:
        updated["repetitions"] = 0
        updated["interval_days"] = 1
        updated["next_review"] = _iso(_add_days(today, 1))
    return updated


def report_card(card):
    """Mark a card reported ("ভুল রিপোর্ট করুন"): reported = true and
    next_review = null, so it leaves the quiz until review."""
    updated = dict(card)
    updated["reported"] = True
    updated["next_review"] = None
    return updated


def quiz_due(cards, today):
    """Cards due on ``today`` — reported cards and cards with no
    next_review are excluded. Yesterday's facts first: sorted by
    next_review, oldest first (then fact_id for stability)."""
    today = _as_date(today)
    due = []
    for card in cards or []:
        if card.get("reported") or not card.get("next_review"):
            continue
        if _as_date(card["next_review"]) <= today:
            due.append(card)
    return sorted(due, key=lambda c: (c["next_review"], c["fact_id"]))
