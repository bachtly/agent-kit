---
name: storybook-mockup
description: Use in agent-kit type:mockup runs to build a clickable UI mockup as Storybook stories with mock data, so the owner can review the look and flows in the PR's Storybook preview before any feature work.
---

# Storybook mockup

The goal is fast visual feedback, not production code. The owner opens the PR's Storybook
preview (published by the app's own CI), comments, and later turns the approved mockup into a
`type:feature` or `type:epic` issue.

## Before you start

- Find the app's Storybook: `.storybook/`, a `storybook` script or dependency in `package.json`.
- **No Storybook:** don't install it (that needs commands this run may not have). Stop with status
  `waiting-for-owner` and propose, in `reply.md`, a `type:chore` issue that adds Storybook, plus the
  preview job (see "Preview" below).
- Read the app's design system: theme tokens, shared components, existing stories. Reuse them.
  New components only where nothing fits.

## What to write

- Location: next to existing stories if the app has a pattern; otherwise
  `src/mockups/<issue>-<slug>/`. Story title prefix: `Mockups/<issue> <feature>/`.
- Presentational components only, driven by props. Mock data in a `*.mocks.*` file next to them.
  No network, no stores, no backend or API changes, no edits to existing app logic.
- One story per screen state: default, empty, loading, error, long content, and a narrow (mobile)
  viewport when the app is responsive. Flows with several screens get one story per step, linked in
  a `Flow` story or listed in the docs page.
- Use the Storybook version's current story format (CSF3 for Storybook 7+). Match the app's
  TypeScript and lint rules so the check command passes.
- UI choices with a real alternative (layout, navigation pattern, component type) are decisions:
  research them with the `web-research` skill, and where two options are close, add both as
  separate stories (`Option A`, `Option B`) for the owner to pick.

## Output

- `reply.md`: the story list (title → what it shows), the options to choose between, and "Open the
  Storybook preview on the PR, comment, then `@agent <changes>` or `@agent approve`."
- On approval: in `reply.md`, draft the follow-up `type:feature` or `type:epic` issue text (goal,
  screens with story titles, data each screen needs). The owner creates it. Status `ready-for-review`.

## Preview (app side, not agent-kit)

The app's own CI publishes Storybook per PR, e.g. a job that runs `build-storybook` and uploads it
to Chromatic or a Pages preview, and links it on the PR. Without it, the owner can run Storybook
locally on the PR branch.
