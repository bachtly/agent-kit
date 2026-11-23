# Setup

One-time setup of the GitHub App and credentials, then the per-repo secrets. Back to the
[README](../README.md).

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
   owner/repo"), or by hand with [ONBOARDING.md](../ONBOARDING.md).

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
