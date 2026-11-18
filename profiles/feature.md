---
model: opus
max_turns: 80
allowed_tools: Read,Write,Edit,Glob,Grep,Skill,Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git add:*),Bash(git commit:*),Bash(git mv:*),Bash(git rm:*)
---

Features run in two phases with one gate between them: the design doc. Work out which phase you
are in from the latest state comment and the conversation.

## Phase 1: design (no approved design yet)

1. Follow the `feature-design` skill: read the request and the code, research the main decision,
   and write the design doc `docs/design/<issue>-<slug>.md`. Commit it. Change no other files.
   The workflow opens the draft PR, so the owner can comment on the doc line by line.
2. In `reply.md`: a 5-line summary of the design, the doc's path, the open questions with your
   recommended answers, and: "Comment inline on the doc in the PR, then reply `@agent approve`
   (or `@agent <changes>`)."
3. Write the state comment with status `design-proposed`. Put the design's key points under Plan.

## Revising the design (the owner asked for changes, did not approve)

Revise the doc as the `feature-design` skill says, commit, and stay in phase 1 with status
`design-proposed`. Inline review comments on the PR count as change requests.

## Phase 2: implement (the owner approved the design in a comment after it)

Approval is any owner comment after the latest design revision that approves it, with or without
changes. Changes that come with the approval go into the doc first.

1. Implement the design. Tests come with the code and cover its acceptance criteria.
2. Run the check command. Commit in logical steps.
3. If the code had to differ from the design, update the doc in the same commit and say why in
   `reply.md`. Set the doc's `Status:` to `implemented`.
4. In `reply.md`, summarize what was built, with the AC → test mapping.
5. Write the state comment with status `ready-for-review`.

If the work doesn't fit in this run, commit what is done and working. Set status `in-progress` and
make the next step precise enough for the next run to continue.
