---
name: slice-plan
description: Use in an agent-kit type:epic run, after the design is approved, to break the epic into slices and write docs/design/<issue>-slices.json, the breakdown the workflow turns into slice issues and PRs.
---

# Slice plan

Each slice becomes an issue, a branch and a PR into the epic branch, run by its own agent run,
in parallel with the others when it has no dependencies. The owner reviews the whole epic PR at
the end. So slices must be small, independent where possible, and each one complete on its own.

## Rules

- 2 to 12 slices. Each fits one agent run (about a day of human work at most).
- Vertical slices that each work end to end (behind a flag if needed) beat horizontal layers.
- A shared contract (schema, API types, interfaces) goes in its own early slice that the others
  depend on. This is what lets the rest run in parallel without conflicts.
- Two slices without a dependency between them must not edit the same files, except small shared
  registrations (routes, exports). Note those in both bodies.
- Every acceptance criterion of the design belongs to exactly one slice.
- Research the slicing choice with the `web-research` skill if there is a real alternative.

## File format

`docs/design/<issue>-slices.json`, a JSON list, in dependency order: a slice may depend only on
slices earlier in the list.

```json
[
  {
    "id": "contract",
    "title": "Booking API types and DB schema",
    "depends_on": [],
    "body": "Goal: ...\n\nACs: AC1, AC2\n\nFiles: src/api/types.ts, migrations/\n\nDesign: docs/design/10-booking.md#data-model"
  },
  {
    "id": "api",
    "title": "Booking endpoints",
    "depends_on": ["contract"],
    "body": "..."
  }
]
```

- `id`: short slug, `a-z`, `0-9`, `-`, unique. `title`: one line, at most 120 characters.
- `body`: Markdown, at most 20,000 characters. Goal, AC ids, the files or modules it owns, and
  links into the design doc. It becomes the slice issue's description, so a fresh run must be able
  to build the slice from it plus the design doc.
- Only these four keys. The workflow rejects anything else, and adds its own labels.

Also add a short Mermaid dependency graph of the slice ids to the design doc's Backend section.
