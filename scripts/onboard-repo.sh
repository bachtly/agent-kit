#!/usr/bin/env bash
# Configure an app repo for agent-kit. Idempotent: safe to re-run.
#
# Usage:
#   scripts/onboard-repo.sh --repo owner/name [--require-review] [--no-environment] \
#     [--client-id ID] [--key-file path/to/app.private-key.pem]
#
# Secrets come from the local environment and are piped to gh on stdin, never printed:
#   AGENT_APP_PRIVATE_KEY_FILE (or --key-file)  GitHub App private key (.pem)
#   CLAUDE_CODE_OAUTH_TOKEN and/or ANTHROPIC_API_KEY
# A secret whose source is unset is skipped, so re-runs don't need every value.
#
# --require-review  add the repo owner as required reviewer on the environment, so every run
#                   waits for approval. Without it, re-running removes any required reviewer.
# --no-environment  fallback for plans without private-repo environments: use repo secrets
#                   (the caller workflow must then pass `environment: ''` and `secrets: inherit`)
set -euo pipefail

ENV_NAME=agent
repo="" require_review=false use_env=true
client_id="${AGENT_APP_CLIENT_ID:-}"
key_file="${AGENT_APP_PRIVATE_KEY_FILE:-}"

die() { echo "error: $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) repo="${2:?}"; shift 2 ;;
    --require-review) require_review=true; shift ;;
    --no-environment) use_env=false; shift ;;
    --client-id) client_id="${2:?}"; shift 2 ;;
    --key-file) key_file="${2:?}"; shift 2 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$repo" ] || die "--repo owner/name is required"
command -v gh > /dev/null || die "gh CLI not found"
gh auth status > /dev/null 2>&1 || die "run 'gh auth login' first"

visibility="$(gh repo view "$repo" --json visibility --jq .visibility)"
default_branch="$(gh repo view "$repo" --json defaultBranchRef --jq .defaultBranchRef.name)"
echo "repo=$repo visibility=$visibility default_branch=$default_branch"

echo "== labels"
label() { gh label create "$1" --repo "$repo" --color "$2" --description "$3" --force > /dev/null && echo "  $1"; }
label agent         5319e7 "Start the agent on this issue"
label agent:working fbca04 "Agent run in progress"
label agent:failed  d93f0b "Last agent run failed; see the comment for the run link"
label type:bug      d73a4a "Agent profile: bug"
label type:feature  a2eeef "Agent profile: feature (plan, then implement)"
label type:chore    cfd3d7 "Agent profile: chore (default)"

secret_flags=()
if [ "$use_env" = true ]; then
  echo "== environment '$ENV_NAME' (deployments from $default_branch only)"
  reviewers=',"reviewers":[]'
  if [ "$require_review" = true ]; then
    owner_id="$(gh api "users/${repo%%/*}" --jq .id)"
    reviewers=",\"reviewers\":[{\"type\":\"User\",\"id\":${owner_id}}],\"prevent_self_review\":false"
    echo "  required reviewer: ${repo%%/*}"
  else
    echo "  required reviewer: none"
  fi
  printf '{"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}%s}' "$reviewers" \
    | gh api -X PUT "repos/$repo/environments/$ENV_NAME" --input - > /dev/null \
    || die "could not create the environment. If your plan lacks environments for private repos, re-run with --no-environment"
  existing="$(gh api "repos/$repo/environments/$ENV_NAME/deployment-branch-policies" --jq '.branch_policies[].name')"
  if ! grep -qxF "$default_branch" <<< "$existing"; then
    gh api -X POST "repos/$repo/environments/$ENV_NAME/deployment-branch-policies" \
      -f name="$default_branch" -f type=branch > /dev/null
  fi
  echo "  branch policy: $default_branch"
  secret_flags=(--env "$ENV_NAME")
fi

echo "== variable"
if [ -n "$client_id" ]; then
  gh variable set AGENT_APP_CLIENT_ID --repo "$repo" --body "$client_id" && echo "  AGENT_APP_CLIENT_ID"
else
  echo "  AGENT_APP_CLIENT_ID skipped (pass --client-id)"
fi

echo "== secrets (${secret_flags[*]:-repo level})"
set_secret() { # name: value on stdin
  gh secret set "$1" --repo "$repo" ${secret_flags[@]+"${secret_flags[@]}"} > /dev/null && echo "  $1 set"
}
if [ -n "$key_file" ]; then
  [ -r "$key_file" ] || die "cannot read key file: $key_file"
  set_secret AGENT_APP_PRIVATE_KEY < "$key_file"
else
  echo "  AGENT_APP_PRIVATE_KEY skipped (pass --key-file)"
fi
for name in CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_API_KEY; do
  if [ -n "${!name:-}" ]; then
    printf '%s' "${!name}" | set_secret "$name"
  else
    echo "  $name skipped (not set locally)"
  fi
done

echo "done."
