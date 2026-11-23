# Onboarding an app repo

Checklist version of `.claude/skills/onboard-app/SKILL.md`. Easiest path: open Claude Code in this
repo and say "onboard owner/repo". Keep this file and the skill in sync.

- [ ] **Inspect the repo.** Find its real install/build/test/lint commands. Look in
      `.github/workflows/` first, then `package.json` scripts and lockfile, `*.sln`/`*.csproj`,
      `pyproject.toml`, `Makefile`. Check visibility:
      `gh repo view owner/repo --json visibility,defaultBranchRef`. Note whether it has Storybook
      and whether CI already publishes a Storybook preview on PRs.
- [ ] **Write the app's `CLAUDE.md`** from `templates/app-repo/CLAUDE.md`: one check command,
      a short architecture, do-nots.
- [ ] **Write `.claude/settings.json`** from the template: `permissions.allow` lists exactly the
      commands in `CLAUDE.md`. No `Bash(*)`, `gh`, `curl` or deploy commands.
- [ ] **Install the GitHub App** on the repo (App settings → Install App).
- [ ] **Public repo?** Create a separate Console workspace API key with a monthly spend limit and use
      it as `ANTHROPIC_API_KEY` for this repo.
- [ ] **Run the setup script** with secrets exported locally (never paste them into chat):
      ```sh
      export CLAUDE_CODE_OAUTH_TOKEN=...        # or ANTHROPIC_API_KEY=...
      scripts/onboard-repo.sh --repo owner/repo --client-id Iv23... --key-file ~/keys/agent.pem [--require-review]
      ```
      It creates the labels, the `agent` environment (default branch only, plus you as required
      reviewer with `--require-review`), the `AGENT_APP_CLIENT_ID` variable and the environment secrets.
      If environments aren't available on your plan, use `--no-environment` and the fallback caller in `docs/setup.md`.
- [ ] **Open a PR in the app repo** adding `.github/workflows/agent.yml` (from
      `templates/app-repo/`, with `node_version`/`python_version`/`dotnet_version` and
      `setup_command` set to match CI), `CLAUDE.md` and `.claude/settings.json`. If the app has
      Storybook and no PR preview yet, also add `.github/workflows/storybook-preview.yml` from the
      template (node version, install step and build script matching CI), so the agent's mockup and
      `Option A/B` stories show up as a link on the PR. Merge it.
- [ ] **Storybook preview:** after its first run, set Settings → Pages → Deploy from a branch →
      `gh-pages` / root. No Pages (private repo on a free plan)? Delete the template's `publish` and
      `cleanup` jobs and download the `storybook` artifact instead.
- [ ] **Test:** open an issue "Add a one-line 'Maintained with agent-kit' note to the end of
      README.md", add `type:chore`, then `agent`. Expect `agent:working`, an Actions run (approve
      it if you used `--require-review`), a draft PR from `agent/issue-<N>`, and a reply plus a state comment.
      Then comment `@agent also bold it` to test a follow-up run.
- [ ] **Floods on public repos:**
      `gh api -X PUT repos/owner/repo/interaction-limits -f limit=collaborators_only -f expiry=one_week`.
