# agent-kit

An unattended issue-to-PR agent for your GitHub repos, built on
[`anthropics/claude-code-action`](https://github.com/anthropics/claude-code-action).

You label an issue `agent`. A GitHub Actions run picks it up, Claude works on a branch, the
workflow opens a draft PR, and the agent reports back with comments. To steer it, comment
`@agent ...` on the issue or the PR. No servers and no long-lived sessions.

This repo holds the whole pipeline. Each app repo adds one ~15-line caller workflow plus its own
`CLAUDE.md` and `.claude/settings.json`.

## Architecture

```
app repo                                   agent-kit (this repo, pinned @v1)
────────                                   ─────────────────────────────────
issue labeled `agent` / `@agent` comment
  └─ .github/workflows/agent.yml  ───────▶ .github/workflows/agent.yml (workflow_call)
     (caller: owner-only `if`)               ├─ router/route.py   event → prompt + claude args
                                             ├─ profiles/*.md     per-type steps, model, tools
     CLAUDE.md, .claude/settings.json        ├─ plugins/core      shared skills (plugin marketplace)
     (app context + allowed commands)        └─ claude-code-action runs Claude in the app checkout
```

Configuration has two axes:

| Axis | Selected by | Lives in | Controls |
|---|---|---|---|
| Type | `type:<name>` label (default `chore`) | `profiles/<name>.md` | steps, model, max turns, tool allowlist, extra plugins |
| App | the repo itself | app's `CLAUDE.md`, `.claude/settings.json` | check command, architecture, do-nots, allowed test/lint commands |

Shared skills ship as a Claude Code plugin marketplace (`.claude-plugin/marketplace.json`,
`plugins/core`). Each run loads it from the local checkout at `.agent-kit/`.

### Continuity without sessions

Every trigger is a fresh run. The router rebuilds context from the thread: the issue/PR body,
the latest **state comment** (`<!-- agent-state -->`, written by the agent at the end of every
run: status, branch/PR, plan, decisions, open questions, next step), owner and bot comments,
and inline review comments for PRs. For a PR on `agent/issue-<N>`, it also reads issue N's
comments, so state carries over from issue to PR.

### Ask or proceed

The agent asks 1-3 questions and stops only when a wrong guess would waste the run. Otherwise
it states its assumption and proceeds. `type:feature` runs in two phases: post a plan and stop,
then implement after you reply `@agent approve` (or with changes).

## Run lifecycle

1. **Trigger.** An `issues: labeled` event (label `agent`) or an `issue_comment: created` event
   containing `@agent`. Only the repo owner's events pass the `if`, which also stops the bot's own
   comments from looping. Both event types run from the default branch.
2. **Concurrency.** One run at a time per repo and issue/PR number. Later runs queue; nothing is
   cancelled.
3. **Steps:**
   1. Mint a GitHub App token (expires in 1 hour).
   2. Add `agent:working`, remove `agent` and `agent:failed`, react 👀 to the comment.
   3. Check out the app repo (full history), then agent-kit into `.agent-kit/` (git-excluded).
   4. Route: pick the profile and build the prompt, the `claude_args` and the plugin list.
   5. Check out `agent/issue-<N>` (or the PR's head branch), or create it, with the bot's git identity.
      Install the app's toolchain if the caller asks (`node_version`, `python_version`,
      `dotnet_version`, `setup_command`, e.g. `npm ci`).
   6. Run claude-code-action. Claude edits and commits. It can't push or comment. It writes
      `.agent-out/reply.md` and `.agent-out/state.md` instead.
   7. Push the branch (refused if it touches `.github/workflows/`), open a draft PR if none
      exists, and post the reply and the state comment.
   8. Always remove `agent:working`. On failure, add `agent:failed` and comment the run URL.

## Security model

- **GitHub App token for every write** (not `GITHUB_TOKEN`, not a PAT). CI runs on the agent's
  PRs, and tokens expire after an hour. The App has Contents RW, Issues RW, Pull requests RW,
  Metadata R and **no Workflows permission**, so it cannot push workflow changes even if asked.
- **The agent never holds a write token.** claude-code-action gets the job's `GITHUB_TOKEN`,
  which is `contents: read`. The App token is used only by the workflow's own steps, through a
  one-shot git credential helper, so it is never written to `.git/config`.
- **Tool allowlists** come from the profile (file tools plus `git status/diff/log/add/commit/mv/rm`)
  and the app's `.claude/settings.json` (its test/lint commands). They never include `Bash(*)`,
  `gh`, `curl` or `git push`, and the router rejects `Bash`, `Bash(*)` and `gh api` in profiles.
- **Web tools** are added by the router, never by a profile (it rejects `WebSearch`/`WebFetch` in
  `allowed_tools`). `WebSearch` is on for every run: it sends only query text. `WebFetch` can carry
  data out in a URL, so it is on only when the event says the repo is public. The `web-research`
  skill forbids repo content in queries or URLs and treats fetched pages as untrusted data.
  `--permission-mode default` denies anything not allowed.
- **Trust filter.** Only comments from the repo owner and the App bot reach the prompt. The issue
  body is wrapped as untrusted data. Only the bot's comments count as state.
- **Secrets** sit in an `agent` environment that only the default branch may deploy to. Never put
  deploy or cloud credentials in this job.
- **Public repos:** only the owner's label or `@agent` comment starts a run (the caller's `if:`), so
  runs start without approval. Use a separate Anthropic Console workspace key with a monthly spend
  limit, and switch on GitHub interaction limits during floods. For a manual approval gate on every
  run, use `scripts/onboard-repo.sh --require-review` (adds you as required reviewer).

## One-time setup

1. **Create the GitHub App** (Settings → Developer settings → GitHub Apps → New):
   - Name, e.g. `bachtly-agent`. Homepage: this repo. **Webhook: off.**
   - Repository permissions: Contents **Read & write**, Issues **Read & write**, Pull requests
     **Read & write**, Metadata **Read**. Leave Workflows at *No access*.
   - Where can it be installed: *Only on this account*.
   - After creating it, note the **Client ID** and generate a **private key** (.pem). Keep the file
     outside any repo.
2. **Claude credentials:** run `claude setup-token` to get `CLAUDE_CODE_OAUTH_TOKEN` (uses your
   Claude subscription), or create an `ANTHROPIC_API_KEY` in the Console.
3. **Tag this repo:** `git tag v1 && git push origin v1`. Callers use `@v1`. To roll out a change,
   move the tag: `git tag -f v1 && git push -f origin v1`.
4. **Onboard each app repo** with the `onboard-app` skill (ask Claude Code: "onboard
   owner/repo"), or by hand with [ONBOARDING.md](ONBOARDING.md).

### Secrets and variables (per app repo)

| Name | Kind | Where | Value |
|---|---|---|---|
| `AGENT_APP_CLIENT_ID` | variable | repo | GitHub App Client ID |
| `AGENT_APP_PRIVATE_KEY` | secret | `agent` environment | App private key (.pem contents) |
| `CLAUDE_CODE_OAUTH_TOKEN` | secret | `agent` environment | from `claude setup-token` (set this or the next one) |
| `ANTHROPIC_API_KEY` | secret | `agent` environment | Console API key (recommended for public repos, with a spend limit) |

The `agent` environment has a deployment branch policy that allows only the default branch. With
`--require-review` it also has you as required reviewer, so every run waits for your approval.

The caller must pass `secrets: inherit` (the template does). Without it the reusable workflow sees
empty secrets, even though its job runs in the `agent` environment, and the token step fails with
"The 'private-key' input must be set to a non-empty string".

**Fallback (no environments for private repos on your plan):** run the script with
`--no-environment` to store them as repo secrets, and change the caller to:

```yaml
    uses: bachtly/agent-kit/.github/workflows/agent.yml@v1
    with:
      app_client_id: ${{ vars.AGENT_APP_CLIENT_ID }}
      environment: ''
    secrets: inherit
```

## Using it

| You do | Agent does |
|---|---|
| Open an issue, add `type:bug`/`type:feature`/`type:chore`, then `agent` | Works it on `agent/issue-<N>` and opens a draft PR |
| Comment `@agent <instruction>` on the issue | Follow-up run on the same branch |
| Comment `@agent ...` in a PR's Conversation tab | Run on the PR branch. Its inline review comments are included as `path:line` |
| Reply `@agent approve` to a feature plan | Implements the plan |

Inline review comments don't trigger runs. Leave them, then post one `@agent address the review`.

## Extending

- **New issue type:** add `profiles/<name>.md` with frontmatter (`model`, `max_turns`,
  `allowed_tools`, optional `plugins`), add the `type:<name>` label to `scripts/onboard-repo.sh`,
  and re-run it on your repos.
- **New shared skill:** add `plugins/core/skills/<skill>/SKILL.md`.
- **Stack plugin (e.g. dotnet):** add `plugins/<name>/.claude-plugin/plugin.json` and its skills,
  register it in `.claude-plugin/marketplace.json`, and list it in a profile's `plugins:`
  frontmatter. Profiles are shared by all repos, so stack plugins suit profiles like `dotnet-bug`.
- **App-specific behaviour:** goes in that app's `CLAUDE.md` and `.claude/settings.json`, not here.

## Limits

- Comments only. Inline PR review comments and reviews don't trigger runs.
- The agent can't change `.github/workflows/` (no Workflows permission; the push step refuses).
- Fork PRs are refused.
- One run's work is capped by the profile's `max_turns` and the job timeout (default 60 min).
  Bigger tasks continue over several `@agent continue` runs through the state comment.
- The conversation in the prompt is capped (~60 KB). The oldest comments are dropped first, and
  the state comment is always kept.
- `kit_ref` (default `v1`) must match the tag in the caller's `uses:`. A reusable workflow cannot
  see its own ref.
- Commands that need services (databases, Docker, cloud) aren't available unless the app's own setup
  provides them inside the job.

## Development

```sh
python -m unittest discover -s router -v
shellcheck scripts/*.sh
actionlint
```

CI (`.github/workflows/ci.yml`) runs the same three on every push and PR. See [CLAUDE.md](CLAUDE.md).
