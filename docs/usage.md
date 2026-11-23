# Using agent-kit

What to label and comment, which issue type to pick, and how epics run. Back to the
[README](../README.md).

## What you do, what the agent does

| You do | Agent does |
|---|---|
| Open an issue, add `type:bug`/`type:feature`/`type:chore`, then `agent` | Works it on `agent/issue-<N>` and opens a draft PR |
| Comment `@agent <instruction>` on the issue | Follow-up run on the same branch |
| Comment `@agent ...` in a PR's Conversation tab | Run on the PR branch. Its inline review comments are included as `path:line` |
| Comment inline on a feature's design doc, then `@agent approve` | Applies your changes to the doc, then implements it |
| Open a `type:mockup` issue, then `agent` | Storybook stories with mock data for the screens, reviewed in the PR's Storybook preview (your app's CI publishes it). On approval, drafts the follow-up feature or epic issue |
| Comment `@agent mockup` on any issue or PR | Storybook stories for the UI the task changes, one `Option A/B/...` story per open visual question |
| Open a `type:epic` issue, then `agent` | Design doc → slice breakdown → slice issues that run by themselves → one big epic PR (see below) |

Inline review comments don't trigger runs. Leave them, then post one `@agent address the review`.

## Which type to use

| Work | Label | Your gates |
|---|---|---|
| Bug, colour or theme tweak, button, scrolling | `type:bug` / `type:chore` | the PR |
| Large feature, one PR is fine | `type:feature` | design doc, then the PR |
| Large feature, built in parallel slices, one big PR | `type:epic` | design doc, slice list, then the epic PR |
| Needs visual feedback first | `type:mockup` | the Storybook preview; then open a feature or epic |

Every decision is made from at least two candidates, compared by web research (`web-research`
skill); candidates, queries and sources go under Research in the state comment. When the decision
is yours, `reply.md` lists every candidate with pros and cons and a recommendation, and asks you to
pick.

UI decisions are shown, not described: if the app has Storybook, each candidate gets a story named
`Option A`, `Option B`, ... The preview is hosted on public GitHub Pages (mock data only). To see it
from the PR, add the preview workflow `templates/app-repo/.github/workflows/storybook-preview.yml`
to the app (onboarding does).

## Epics

For a feature too big for one PR, where you still want to review one PR at the end.

```
#10 epic issue (type:epic)  →  #50 epic PR  agent/issue-10 → main      ← you review this
                                 ├─ #51 slice PR  agent/issue-11 → agent/issue-10  (merged by the workflow)
                                 ├─ #52 slice PR  agent/issue-12 → agent/issue-10  (merged by the workflow)
                                 └─ #53 slice PR  agent/issue-13 → agent/issue-10  (after #11, #12)
```

1. **Design.** The first run commits `docs/design/<issue>-<slug>.md` to the epic's draft PR. Comment
   inline, then `@agent approve`.
2. **Breakdown.** The next run commits `docs/design/<issue>-slices.json` (the `slice-plan` skill).
   Comment, then `@agent approve`.
3. **Slices.** The next run hands the list to the workflow (`router/slices.py create`). It validates
   it (at most 12 slices, only `id`, `title`, `body`, `depends_on`, dependencies on earlier slices
   only), creates one `type:slice` issue per slice, and labels the ones without dependencies `agent`.
   Each slice branches from the epic branch and opens a PR into it.
4. **Merge.** When a slice run ends `ready-for-review`, the workflow merges its PR into the epic
   branch (merge commit), closes the slice issue, and starts the slices whose dependencies are now
   all merged. Slices without a dependency between them run in parallel.
5. **Review.** When every slice is in, the workflow marks the epic PR ready and comments on the
   epic. Review the whole feature there; each slice PR stays linked from its issue for tracing back.
   `@agent ...` on the epic PR makes changes on the epic branch.

Only the workflow starts slice runs: the App labels its own slice issues. The caller's `if:` allows
that one bot event, and the kit checks the sender is this App and the issue its own slice.
**Existing callers:** copy the new `if:` from `templates/app-repo/.github/workflows/agent.yml`, or
slices are created but never start. If a slice PR conflicts with slices merged before it, the
workflow comments on the slice; reply `@agent merge the epic branch and resolve the conflicts`.
