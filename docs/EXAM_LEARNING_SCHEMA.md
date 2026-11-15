# News-led exam-learning data contract

This contract defines the optional learning material attached to a news story. It is designed for BCS Preliminary/Written, Bangladesh Bank and other bank recruitment, and relevant government-job examinations.

The learning material must grow naturally from the story. Do not add a generic introductory heading or a detached textbook chapter. Do not generate a duplicate English summary.

## Storage location

Each story may carry an `exam_learning` object:

- In the English canonical edition, use `exam_learning_en` (or `exam_learning`) on the source item.
- In the Bangla overlay, use `exam_learning_bn`.
- The app converter preserves these objects. It does not create, translate, or verify them.
- Bangla material is shown only when the entire story overlay has `translation_status: "approved"`.

## Supported sections

All fields are optional arrays. Omit empty sections.

| Field | Item shape | Purpose |
|---|---|---|
| `concepts` | `{title, body, source_refs[]}` | Definitions and concepts needed to understand the story |
| `institutions` | `{title, body, points[], source_refs[]}` | Relevant agencies, mandates and institutional roles |
| `processes` | `{title, body, points[], source_refs[]}` | Procedures, policy cycles and how something works |
| `distinctions` | `{title, left, right, points[], source_refs[]}` | Commonly confused terms, bodies or instruments |
| `exam_notes` | string or `{text, source_refs[]}` | Compact facts and exam-oriented notes |
| `mcqs` | `{question, options, answer, explanation, source_refs[]}` | One-answer MCQs with explanation |
| `short_questions` | `{question, answer, source_refs[]}` | Factual and conceptual recall |
| `analytical_questions` | `{question, answer_outline, source_refs[]}` | Written/analytical prompts where the story supports them |
| `vocabulary` | `{term, pronunciation_bn, part_of_speech, meaning_bn, definition, synonyms[], antonyms[], example, source_refs[]}` | Useful contextual vocabulary |
| `revision` | string or `{prompt, answer}` | Quick recall and flashcards |

A `source_refs` item should use:
`{title, publisher, url, published_date, accessed_date, source_type}`.

Only use direct, relevant source URLs. Prefer primary sources for laws, official statistics, institutional mandates and government decisions. Use recognised academic or international-organisation sources for stable concepts where appropriate. Record access dates for online sources. If a source cannot be opened or its claim cannot be verified, do not present the claim as established fact.

## MCQ rules

- `options` may be an object keyed by A/B/C/D or ক/খ/গ/ঘ, or an array of option strings.
- `answer` must identify exactly one option key or give the exact answer text.
- Each distractor must be plausible, of the same type as the answer, and demonstrably incorrect.
- The explanation must justify the answer and correct the likely misconception.
- Never use "all of the above", "none of the above", or ambiguous negative stems.
- Vary the correct-option position across a set.
- Do not generate questions from unsupported article claims or unverified background.

## Editorial and publication gates

1. Keep reported news facts separate from researched background.
2. Attach source references to every material external fact, definition, institutional role, date or figure.
3. Mark time-sensitive facts with an explicit as-of date.
4. Never invent sources, citations, laws, figures, institutional responsibilities or exam trends.
5. Use natural Bangla as the default reader experience. Retain English terminology when it helps the learner identify the official term.
6. Do not create a separate English article summary that repeats the Bangla explanation.
7. If the Bangla learning layer is incomplete or unreviewed, do not silently substitute English prose in the Bangla edition.
8. Empty or missing learning sections are acceptable. Accurate coverage is more valuable than filling every field.

## Example

```json
{
  "exam_learning_bn": {
    "concepts": [
      {
        "title": "বার্ষিক উন্নয়ন কর্মসূচি (ADP)",
        "body": "এক অর্থবছরে সরকার যে উন্নয়ন প্রকল্পগুলো বাস্তবায়নের জন্য গ্রহণ করে, সেগুলোর সমন্বিত কর্মসূচি।",
        "source_refs": [
          {
            "title": "Official planning document",
            "publisher": "Bangladesh Planning Commission",
            "url": "https://example.gov.bd/document",
            "accessed_date": "2026-11-16",
            "source_type": "primary"
          }
        ]
      }
    ],
    "distinctions": [
      {
        "title": "ADP ও RADP",
        "left": "ADP: মূল বার্ষিক উন্নয়ন কর্মসূচি",
        "right": "RADP: সংশোধিত বার্ষিক উন্নয়ন কর্মসূচি"
      }
    ],
    "mcqs": [
      {
        "question": "ADP-ভুক্ত প্রকল্পের বাস্তবায়ন পরিবীক্ষণ করে কোন বিভাগ?",
        "options": {"ক": "IMED", "খ": "বাংলাদেশ ব্যাংক", "গ": "BBS", "ঘ": "ERD"},
        "answer": "ক",
        "explanation": "IMED উন্নয়ন প্রকল্পের বাস্তবায়ন অগ্রগতি পরিবীক্ষণ ও মূল্যায়ন করে।",
        "source_refs": []
      }
    ]
  }
}
```

The example is a structural illustration, not approved study content. Replace the placeholder source with an opened, authoritative source before publication.
