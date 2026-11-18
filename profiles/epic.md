---
model: opus
max_turns: 80
allowed_tools: Read,Write,Edit,Glob,Grep,Skill,Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git add:*),Bash(git commit:*),Bash(git mv:*),Bash(git rm:*)
---

An epic is a large feature built as several slices. Its branch `agent/issue-<epic>` and its draft
PR into the default branch hold the design and, in the end, the whole feature: every slice PR is
merged into this branch. The owner reviews that one big PR and traces back to slice PRs if needed.

Gates: design → breakdown → slices run → final review. Work out the phase from the latest state
comment and the conversation. An approval is an owner comment after the latest revision that
approves it, with or without changes. Inline review comments on the epic PR count as change
requests.

## Phase 1: design (no approved design yet)

Exactly as `type:feature` phase 1: follow the `feature-design` skill, commit
`docs/design/<issue>-<slug>.md`, change no other files. Revise it on change requests.
In `reply.md`: a 5-line summary, the doc path, open questions with your recommended answers, and
"Comment inline on the doc, then reply `@agent approve` (or with changes)."
Status `design-proposed`.

## Phase 2: breakdown (design approved, no approved breakdown yet)

1. Apply any changes that came with the approval to the design doc.
2. Follow the `slice-plan` skill: commit the breakdown `docs/design/<issue>-slices.json`.
   Revise it on change requests.
3. In `reply.md`: the slices as a table (id, title, depends on, one-line goal) and "Reply `@agent
   approve` to create the slice issues. They start automatically."
4. Status `breakdown-proposed`.

## Phase 3: create slices (breakdown approved)

1. Apply any changes that came with the approval to `docs/design/<issue>-slices.json` and commit.
2. Copy it, unchanged, to `.agent-out/slices.json`. The workflow validates it, creates one
   `type:slice` issue per slice, and starts those without dependencies. Do not write code.
3. In `reply.md`: "Creating N slice issues." Status `in-progress`. Next step: "Wait for the slices.
   The workflow comments here when every slice is merged into this branch."

Write `.agent-out/slices.json` only in this phase, and only once. If the conversation shows the
slice issues were already created, don't write it again.

## Phase 4: final review (slice issues exist)

The owner comments on the epic PR or issue. Make the requested changes directly on this branch,
across slices if needed, and keep the design doc in sync. Run the check command. In `reply.md`,
summarize the changes. Status `ready-for-review`.
If the owner asks about a slice that is still running, say which one and stop (status `in-progress`).
