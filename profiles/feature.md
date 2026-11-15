---
model: opus
max_turns: 80
allowed_tools: Read,Write,Edit,Glob,Grep,Skill,Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git add:*),Bash(git commit:*),Bash(git mv:*),Bash(git rm:*)
---

Features run in two phases. Use the latest state comment and the conversation to work out which
phase you are in.

## Phase 1: plan (no approved plan yet)

1. Read the request and explore the code it touches.
2. Write a plan in `reply.md`: the approach, the files to change, data or API changes, tests, and
   any open questions. Keep it short enough to review in two minutes.
3. Do not change code. Write the state comment with status `plan-proposed` and the plan's key
   points under Plan.
4. End the reply with: "Reply `@agent approve` (or with changes) to start implementing."

## Phase 2: implement (the owner approved the plan in a comment after it)

Approval is any comment from the owner, posted after the plan, that approves it, with or without
changes. If the owner asked for changes instead of approving, revise the plan and stay in phase 1.

1. Implement the approved plan, including any changes the owner asked for. Tests come with the code.
2. Run the check command. Commit in logical steps.
3. In `reply.md`, summarize what was built and anything that differs from the plan, with the reason.
4. Write the state comment with status `ready-for-review`.

If the work doesn't fit in this run, commit what is done and working. Set status `in-progress` and
make the next step precise enough for the next run to continue.
