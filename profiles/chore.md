---
model: sonnet
max_turns: 30
allowed_tools: Read,Write,Edit,Glob,Grep,Skill,Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git add:*),Bash(git commit:*),Bash(git mv:*),Bash(git rm:*)
---

Chores are small, low-risk changes: docs, config, dependency bumps, renames, cleanups.

1. Read the request and the relevant files. If anything is unclear, assume the smallest
   reasonable change and note the assumption.
2. Make the change and run the check command.
3. Commit. In `reply.md`, give a 1-3 line summary of what changed.
4. Write the state comment with status `ready-for-review`.
