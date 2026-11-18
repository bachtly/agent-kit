---
name: feature-design
description: Use in agent-kit type:feature and type:epic runs to write or revise the design doc docs/design/<issue>-<slug>.md, which the owner reviews inline in the draft PR before any code is written. Unattended version of the interactive feature-design workflow.
---

# Feature design doc (unattended)

The owner reviews the design as a file in the draft PR, with inline comments, and approves it
with `@agent approve`. Nobody answers questions during the run: open questions go in the doc
and in `reply.md`, each with your recommended answer, and you proceed on that recommendation.

## Where

- `docs/design/<issue>-<slug>.md`, unless the repo's `CLAUDE.md`, README or `docs/` say design
  docs go elsewhere. Then follow the repo.
- ADRs go in the repo's ADR folder if it has one (continue its numbering). Otherwise they are
  rows in the doc's Decisions table, not separate files.

## Steps

1. Read the request, the repo's canonical docs (`CLAUDE.md`, README, `docs/`, existing ADRs) and the
   code the feature touches. The repo's docs win over generic practice.
2. Research the main decision with the `web-research` skill: how products, open source and
   standards solve this job. Keep the rejected options for "Alternatives considered".
3. Write the doc from the template below. Skip a section that doesn't apply with one line saying
   why. **Size limit: about 1,200 words** (a 10-minute review). Link `path:line` instead of
   pasting code.
4. Self-review before committing, as a critic would. Fix what fails:
   - Every requirement has an acceptance criterion (AC id) that a test can check.
   - Names, types and ids agree across sections. One term per concept.
   - At least one rejected alternative, with the reason.
   - Pre-mortem: "six months later this failed: why?" Each answer is mitigated or listed as a risk.
5. Commit the doc alone (`Design: <feature>`).

## Revising

Inline review comments arrive as `path:line`. Address each one: change the doc, or answer in
`reply.md` why not. Keep a short `## Changes` list at the end of the doc (one line per revision
round). Never edit sections the owner didn't ask about, except to keep the doc consistent.

## Template

```markdown
# <Feature>: design

Status: proposed · Issue: #<n> · Date: <YYYY-MM-DD>

## Context and scope
## Goals and non-goals
## Requirements            (R1.. with acceptance criteria AC1..; main flows and edge cases)
## Design
### Data model             (tables/fields/migrations, or "no change")
### API                    (endpoints, types, errors, or "no change")
### UI                     (screens, states: empty/loading/error, accessibility)
### Backend                (modules, concurrency, failure handling, rollout/flag)
## Alternatives considered (option → why rejected)
## Research                (questions → choice, with queries and source links)
## Cross-cutting concerns  (security, privacy, observability, cost)
## Tests                   (which AC each test covers)
## Risks and open questions (each with your recommended answer)
## Decisions               (| # | decision | alternative | reason |)
```
