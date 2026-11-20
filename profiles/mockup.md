---
model: sonnet
max_turns: 60
allowed_tools: Read,Write,Edit,Glob,Grep,Skill,Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git add:*),Bash(git commit:*),Bash(git mv:*),Bash(git rm:*)
---

A mockup is a set of Storybook stories with mock data, for visual feedback before a feature is
designed or built. Follow the `storybook-mockup` skill. No app logic, backend or API changes.

1. Read the request and the app's UI code, design system and existing stories.
2. Write the stories and their presentational components. Run the check command.
3. Commit. In `reply.md`, list the stories and, per open question, the `Option A/B/...` stories to
   pick between.
4. Status `ready-for-review`.

Change requests (comments, inline review on the PR) and option picks revise the stories, with the
same status.
When the owner approves, draft the follow-up `type:feature` or `type:epic` issue in `reply.md`, as
the skill says.
