---
name: storybook-mockup
description: Use in any agent-kit run that builds Storybook stories for the owner to look at - every type:mockup run, any run where the owner asks for a mockup, and any run with an open question or decision that changes the UI (one story per option). The owner reviews them in the PR's Storybook preview.
---

# Storybook mockup

The goal is fast visual feedback. The owner opens the PR's Storybook preview (published by the
app's own CI), compares the options, and picks one in a comment.

When this applies:

- **`type:mockup` run:** the whole run is the mockup. Mock data only, no app logic. On approval it
  becomes a `type:feature` or `type:epic` issue.
- **The owner asks for a mockup in another profile** (e.g. `@agent mockup ?` on a bug): mock up
  the UI this task changes, with one story per option for every open visual question. Don't stop
  at the one design you chose.
- **An open question or decision changes the UI** (layout, label vs icon, component type,
  navigation pattern): one story per candidate, even if nobody asked for a mockup.

## Before you start

- Find the app's Storybook: `.storybook/`, a `storybook` script or dependency in `package.json`.
- **No Storybook:** don't install it (that needs commands this run may not have). In `reply.md`,
  describe each option in words and propose a `type:chore` issue that adds Storybook plus the
  preview job (see "Preview" below). A `type:mockup` run stops there with status
  `waiting-for-owner`. Other profiles continue on their recommended option.
- Read the app's design system: theme tokens, shared components, existing stories. Reuse them.
  New components only where nothing fits.

## What to write

- Location: next to existing stories if the app has a pattern; otherwise
  `src/mockups/<issue>-<slug>/`. Story title prefix: `Mockups/<issue> <feature>/`.
- In a `type:mockup` run: presentational components only, driven by props. Mock data in a
  `*.mocks.*` file next to them. No network, no stores, no backend or API changes, no edits to
  existing app logic. In other profiles, stories may render the real components you are changing,
  with mock props.
- One story per screen state: default, empty, loading, error, long content, and a narrow (mobile)
  viewport when the app is responsive. Flows with several screens get one story per step, linked in
  a `Flow` story or listed in the docs page.
- Use the Storybook version's current story format (CSF3 for Storybook 7+). Match the app's
  TypeScript and lint rules so the check command passes.

## Options

- Every UI choice with a real alternative is a decision: research it with the `web-research`
  skill. Each candidate that survives research gets its own story, named `Option A <what>`,
  `Option B <what>` (e.g. `Option A Icon only`, `Option B Icon and label`). Same mock data and
  viewport in each, so only the option differs.
- Build every candidate, including the ones you don't recommend. A question about the UI with one
  rendered answer is not a choice.
- Outside `type:mockup`, implement your recommended option in the app code and say so. Once the
  owner picks, implement that option and delete the other options' stories.

## Output

- `reply.md`: the story list (title → what it shows), then for each open question a table of
  options (story title, what differs, your recommendation), and "Open the Storybook preview on the
  PR, comment with your pick or changes (`@agent option B`, `@agent approve`)."
- In the state comment, list each unanswered option question under Open questions.
- `type:mockup` approval: in `reply.md`, draft the follow-up `type:feature` or `type:epic` issue
  text (goal, screens with story titles, data each screen needs). The owner creates it. Status
  `ready-for-review`.

## Preview (app side, not agent-kit)

The app's own CI publishes Storybook per PR and links it on the PR. agent-kit ships a template:
`templates/app-repo/.github/workflows/storybook-preview.yml` (build on every PR, publish to
`gh-pages` under `pr-<N>/`, comment the link). The agent can't add it: it can't change
`.github/workflows/`. If the PR has no preview link, say in `reply.md` that the owner can add that
template, or run Storybook locally on the PR branch.
