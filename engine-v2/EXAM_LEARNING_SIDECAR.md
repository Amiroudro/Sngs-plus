# Exam-learning sidecar workflow

The v2 news pipeline collects and verifies reporting. It does not independently research a full topic lesson. To add the broader exam-learning layer, an editor or research assistant creates a separate, source-linked sidecar after the story IDs are known.

## File name and location

Place this file in the run directory:

`exam-learning-YYYY-MM-DD.json`

The date must match the edition being converted. The converter reads it automatically. If the file is absent, the conversion continues with no added topic notes. If its date or structure is invalid, conversion stops rather than silently dropping or misattaching the notes.

## Structure

```json
{
  "edition_date": "2026-11-16",
  "stories": {
    "V2-STORY-ID": {
      "en": {
        "concepts": [],
        "institutions": [],
        "processes": [],
        "distinctions": [],
        "exam_notes": [],
        "mcqs": [],
        "short_questions": [],
        "analytical_questions": [],
        "vocabulary": [],
        "revision": []
      },
      "bn": {
        "concepts": [],
        "institutions": [],
        "processes": [],
        "distinctions": [],
        "exam_notes": [],
        "mcqs": [],
        "short_questions": [],
        "analytical_questions": [],
        "vocabulary": [],
        "revision": []
      }
    }
  }
}
```

Use the original v2 story ID as the key, not the app's CA01/CA02 display ID. The converter maps it to the corresponding app story ID.

## Workflow

1. Run the normal v2 collection and editorial pipeline.
2. Select stories with genuine syllabus value. Do not add a topic lesson to every minor story.
3. Research relevant concepts from official/primary sources first: laws, gazettes, ministry pages, regulators, Bangladesh Bank, Planning Commission, BBS, Parliament, courts and official datasets. Use reputable academic and international-organisation sources for stable concepts.
4. Record a source reference for every material external fact. Include the exact page/report title, publisher, URL and access date.
5. Prepare natural Bangla learning notes. Retain English official names and abbreviations where they help candidates recognise the term.
6. Write MCQs with one defensible answer, plausible same-type distractors and an explanation. Check every option and answer against the source.
7. Add the Bangla layer only after it has been checked. The existing story-level `translation_status: "approved"` gate still controls whether the Bangla story and its learning notes can appear in the Bangla app.
8. Convert to app format. Inspect the conversion report's `exam_learning` counts and the generated JSON before human approval.

## Important

- The converter only validates the sidecar's outer structure and attaches the supplied objects. It does not fetch URLs, fact-check claims, translate text or approve publication.
- No source permission is implied by the ability to open a webpage.
- A missing sidecar is not a conversion failure. It means that no expanded learning notes were prepared for that edition.
- Never copy a generic lesson across unrelated stories without checking that it actually explains the story.
