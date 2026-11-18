# agent-kit

Central repo for an unattended issue-to-PR agent on `anthropics/claude-code-action@v1`.
App repos call `.github/workflows/agent.yml` (`workflow_call`) pinned at `@v1`. Read README.md for
the architecture and run lifecycle.

## Check command

```sh
python -m unittest discover -s router -v && shellcheck scripts/*.sh && actionlint
```

## Map

- `.github/workflows/agent.yml`: the reusable workflow. Owns every GitHub write: labels, push,
  PR, comments.
- `router/route.py`: stdlib-only. Event → `prompt`, `claude_args`, `plugins`, `profile`, `ref`,
  `is_pr`, `issue`. `router/test_route.py` fakes the `gh` API. Add a test for every behaviour change.
- `profiles/_base.md`: rules for every run. `profiles/<type>.md`: frontmatter plus steps.
- `plugins/core`: shared skills, served by `.claude-plugin/marketplace.json` (marketplace name `agent-kit`).
- `scripts/onboard-repo.sh`: idempotent per-repo setup. `.claude/skills/onboard-app`: the onboarding procedure.
- `templates/app-repo/`: files copied into app repos.

## Invariants (don't break)

- The agent never gets a write-capable token. claude-code-action gets `github.token`
  (contents: read). The App token is used only by workflow steps, via a credential helper,
  never persisted.
- Profiles never allow `Bash`, `Bash(*)`, `gh`, `curl` or `git push`. The router enforces part of this.
- Web tools come from the router only: `WebSearch` always, `WebFetch` only on public repos.
- Only comments from the repo owner and the App bot reach the prompt. Only bot comments count as state.
- The App has no Workflows permission. The push step refuses `.github/workflows/` changes.
- `ONBOARDING.md` mirrors `.claude/skills/onboard-app/SKILL.md`.

## Releasing

Changes reach app repos when `v1` moves: `git tag -f v1 && git push -f origin v1`. Breaking
changes to the caller interface need `v2` and a README migration note. Don't tag or push unless asked.
