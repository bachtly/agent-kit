---
model: sonnet
max_turns: 80
allowed_tools: Read,Write,Edit,Glob,Grep,Skill,Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git add:*),Bash(git commit:*),Bash(git mv:*),Bash(git rm:*),Bash(git merge:*)
---

A slice is one part of an epic whose design the owner has already approved. There is no plan
gate: implement it. Your branch started from the epic branch (see "This run"), so the design doc
is in `docs/design/`. When you finish with status `ready-for-review`, the workflow merges your PR
into the epic branch and starts the slices that depend on yours. The owner reviews the result in
the epic PR, not here.

1. Read the slice's issue (task description), the epic's design doc and the breakdown
   `docs/design/<epic>-slices.json`. Your slice's `id` is in the task description.
2. Build only this slice. Other slices are built in parallel by other runs: don't touch what the
   breakdown gives to them. If this slice can't be done without that, stop with status
   `waiting-for-owner` and say what overlaps.
3. Tests come with the code and cover the slice's acceptance criteria. Run the check command.
4. Before your final commit, run `git merge --no-edit origin/<epic branch>` to take in slices merged
   since you started. Resolve conflicts, keeping both slices' intent, and run the check command again.
5. Commit. In `reply.md`, give what was built and the AC → test mapping, in 3 to 8 lines.
6. Status `ready-for-review` only when the slice is complete and the check command passes.
   Otherwise `in-progress` (the next run continues) or `blocked`. Only `ready-for-review` is merged.

Research decisions inside the slice the same way as any other run. Decisions already settled in the
design doc need no new research.
