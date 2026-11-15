---
model: sonnet
max_turns: 50
allowed_tools: Read,Write,Edit,Glob,Grep,Skill,Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git add:*),Bash(git commit:*),Bash(git mv:*),Bash(git rm:*)
---

Bug fixes: find the root cause, prove it with a test, fix it.

1. Reproduce the bug from the description. Locate the root cause, not just the symptom.
2. Write a failing test that captures the bug, if the repo has tests for that area.
3. Fix it with the smallest change that addresses the root cause. Run the check command.
4. Commit. In `reply.md`, give the root cause in one or two sentences, the fix, and the test that covers it.
5. Write the state comment with status `ready-for-review`.

If you cannot reproduce the bug or locate the cause, don't guess at a fix. Report what you checked
and ask for the missing detail (status `waiting-for-owner`).
