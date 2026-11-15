---
name: onboard-app
description: When asked to onboard, add, or connect an app repo to the agent, run this procedure.
---

# Onboard an app repo to agent-kit

Input: a target repo, as a local clone path or `owner/name`. If only one is given, find the
other (`git -C <path> remote get-url origin`, or `gh repo clone owner/name` into a scratch dir).
`ONBOARDING.md` is the human-readable version of this procedure. Keep the two in sync.

Stop and wait for the user at each **WAIT**.

## 1. Inspect the target (read-only)

Find the real commands. Never invent them. Look in this order and note the file each command
came from:

- `package.json` `scripts`, plus the lockfile to pick the package manager (`pnpm-lock.yaml` → pnpm,
  `yarn.lock` → yarn, `bun.lockb`/`bun.lock` → bun, `package-lock.json` → npm). Workspaces/monorepo?
- `*.sln` / `*.csproj` → `dotnet build`, `dotnet test`; `dotnet format --verify-no-changes` if used.
- `pyproject.toml` / `setup.cfg` / `tox.ini` / `noxfile.py` → tool (uv, poetry, pip), pytest, ruff, mypy.
- `Cargo.toml`, `go.mod`, `Gemfile`, `build.gradle*`, `pom.xml` as applicable.
- `Makefile` / `justfile` / `Taskfile.yml` targets.
- `.github/workflows/*.yml`: **the most reliable source**, because these are the commands CI
  actually runs. Prefer them when they differ from the other sources.
- Existing `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `README.md` for architecture and rules.
- Visibility: `gh repo view <owner/name> --json visibility,defaultBranchRef`.

If a command needs services the agent job won't have (database, Docker, cloud credentials), leave
it out of the check command and say so.

## 2. Propose the app's files. **WAIT** for OK.

Fill `templates/app-repo/CLAUDE.md` and `templates/app-repo/.claude/settings.json`:

- `CLAUDE.md`: one check command (the fast, CI-equivalent chain, e.g. `pnpm lint && pnpm test`),
  a 3-8 bullet architecture, and do-nots specific to this repo.
- `settings.json`: one `permissions.allow` entry per exact command in the check command and its
  steps. Use `Bash(<cmd>:*)` only where arguments vary (e.g. test filters). Keep the deny list.
  Never allow `Bash(*)`, `gh`, `curl`, or deploy/publish commands.
- If the repo already has a `CLAUDE.md` or `.claude/settings.json`, merge into it. Don't replace it.
- Caller `with:` inputs so the check command can run: `node_version` / `python_version` /
  `dotnet_version` (copy the version CI uses) and `setup_command` (the CI install step, e.g.
  `npm ci`). Without them the runner's default toolchain is used and nothing is installed.

Show both files and the caller `with:` block in full, plus a short table of command → source file. Then wait.

## 3. Manual steps the user must do. **WAIT** for confirmation.

- Install the agent GitHub App on this repo (App settings → Install App → choose the repo).
- Have the App's Client ID and private key `.pem` path ready, and `CLAUDE_CODE_OAUTH_TOKEN`
  (from `claude setup-token`) or `ANTHROPIC_API_KEY` exported in their shell.
- **Public repo:** recommend a separate Anthropic Console workspace API key with a monthly spend
  limit for this repo, rather than their personal subscription token. Explain that anyone can open
  issues, but only the owner's label or comment starts a run, and the environment's required
  reviewer means the owner approves each run.

## 4. Run the setup script

```sh
scripts/onboard-repo.sh --repo <owner/name> --client-id <id> --key-file <path.pem> [--public]
```

Add `--public` when the repo is public. Add `--no-environment` only if environment creation fails
on a private repo (plan limitation). Then the caller must use `environment: ''` and
`secrets: inherit` (see README). Never echo, cat or log secret values or the key file. The
script reads them from env/file and pipes them to `gh`.

## 5. Open the PR in the target repo

On a branch `agent-kit-onboarding` in the target clone, add:

- `.github/workflows/agent.yml` from `templates/app-repo/.github/workflows/agent.yml` (unchanged,
  except the fallback edits from step 4 if used)
- the approved `CLAUDE.md` and `.claude/settings.json`

Commit, push, `gh pr create`. Then tell the user how to test after merging:

1. Create an issue: "Add a one-line 'Maintained with agent-kit' note to the end of README.md".
2. Add labels `type:chore`, then `agent`.
3. Expect: 👀 or `agent:working` label → a run under Actions (approve it if the repo is public) →
   a draft PR from `agent/issue-<N>` → a reply and a state comment on the issue.
4. Comment `@agent also bold it` to test a follow-up run on the same branch.

If a flood of issues or comments hits a public repo, suggest temporary interaction limits:
`gh api -X PUT repos/<owner/name>/interaction-limits -f limit=collaborators_only -f expiry=one_week`.

## 6. Suggest shared plugins (don't create them)

If the stack has conventions worth sharing across repos (e.g. dotnet, sveltekit, a test framework
the agent keeps getting wrong), suggest a plugin under `plugins/<name>/`, added to
`.claude-plugin/marketplace.json` and listed in a profile's `plugins:` frontmatter. Create it only
if asked.
