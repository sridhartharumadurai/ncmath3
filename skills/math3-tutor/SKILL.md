---
name: math3-tutor
description: "Run Math 3 (NC) drills: quizzes, EOC mixed practice, progress digests. Use when he asks to be quizzed or wants progress."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [tutoring, math, education]
---

# Math 3 (NC) drills and progress

Syllabus: 10 units, 78 lessons — full id/title map in `references/syllabus.json`
(load it before building any quiz). Lesson id format: `Unit.Lesson` (e.g. 5.2).

## Quiz flow ("quiz me", /quiz)
1. Read `progress.jsonl` (workspace) to find his current unit — the highest
   unit with recent activity; default to Unit 1 if empty.
2. 3 problems: ~70% current unit, ~30% spiral review of units with
   `struggled`/`gave-up` entries. One problem per message; wait for his attempt.
3. Grade each attempt with the hint ladder in SOUL.md; log each problem to
   `progress.jsonl` when done.

## EOC drill ("eoc")
Mixed 5-problem set across all 10 units, weighted toward `struggled` topics.

## Progress digest ("progress", "how am I doing")
Parse the last 7 days of `progress.jsonl`, group by unit and result, and
report in report-card language, one line per unit. End with one specific
suggestion for tonight's review.

## Weekly parent digest
If asked to schedule: weekly cron delivering the digest to the home channel,
built only from `progress.jsonl` — never include conversation text.
