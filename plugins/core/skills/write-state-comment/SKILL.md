---
name: write-state-comment
description: Use at the end of every agent-kit run, including runs that stop early to ask questions, to write .agent-out/state.md, the state comment the next run starts from.
---

# Write the state comment

The next run starts with no memory. This file is everything it will know about the work so far,
besides the conversation. Write it for that reader: precise, short, no narrative.

Write it to `.agent-out/state.md` (create the directory if needed). The workflow adds the
`<!-- agent-state -->` marker and posts it, so don't add the marker yourself. Use exactly this
structure:

```markdown
## Agent state

**Status:** <one of: plan-proposed | waiting-for-owner | in-progress | ready-for-review | blocked>
**Profile:** <bug | feature | chore | ...>
**Branch:** `<branch>` · **PR:** <#number, or "opened by workflow after this run">

### Plan
- [x] done step
- [ ] remaining step

### Decisions
- <decision>: <one-line reason>. Include assumptions you made instead of asking.

### Open questions
- <question for the owner, or "None">

### Next step
<One or two sentences: exactly what the next run should do first.>
```

Rules:
- Carry forward decisions and plan items from the previous state comment unless they changed.
- Status `waiting-for-owner` or `plan-proposed` means the next run must start by reading the
  owner's reply.
- Status `blocked` means you cannot continue without something only the owner can do (access,
  workflow edits, credentials). Say what that is under Open questions.
- Keep it under about 40 lines. Link to files as `path:line` instead of pasting code.
