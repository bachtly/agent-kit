#!/usr/bin/env python3
"""Epic slices. Run by workflow steps with the App token, never by the agent.

  slices.py create   after an epic run: turn .agent-out/slices.json into slice issues and
                     start the ones without dependencies (label `agent`).
  slices.py land     after a slice run that ended `ready-for-review`: merge the slice PR into
                     the epic branch, close the slice issue, start slices whose dependencies
                     are now all merged, and when every slice is in, mark the epic PR ready.

Env: REPO, ISSUE (the run's origin issue), AGENT_BOT_LOGIN, GH_TOKEN (for gh);
     land also EPIC and PR (the slice PR number, may be empty).
Python stdlib only.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import route  # noqa: E402

OUT = Path(".agent-out")
MAX_SLICES = 12
MAX_TITLE = 120
MAX_BODY = 20_000
SLICE_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,30}")
WAITING = "slice:waiting"
MERGE_ATTEMPTS, MERGE_RETRY_SECONDS = 3, 5  # mergeability is computed lazily after PR creation
STATUS = re.compile(r"^\*\*Status:\*\*\s*`?([a-z-]+)", re.M)


class GhError(Exception):
    pass


class GhApi(route.GhApi):
    def request(self, method, path, body=None):
        cmd = ["gh", "api", "-X", method, path]
        if body is not None:
            cmd += ["--input", "-"]
        result = subprocess.run(cmd, input=None if body is None else json.dumps(body),
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise GhError((result.stderr or result.stdout).strip())
        return json.loads(result.stdout) if result.stdout.strip() else None

    def pr_ready(self, repo, number):
        # Draft → ready has no REST endpoint; gh uses GraphQL.
        subprocess.run(["gh", "pr", "ready", str(number), "-R", repo], check=True, capture_output=True, text=True)


def validate(data):
    """Check the agent-written slice list. Returns it normalised, or exits with the first problem."""
    def fail(msg):
        raise SystemExit(f"slices.json: {msg}")

    if not isinstance(data, list) or not 1 <= len(data) <= MAX_SLICES:
        fail(f"must be a list of 1 to {MAX_SLICES} slices")
    seen, out = set(), []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            fail(f"slice {i} is not an object")
        extra = set(item) - {"id", "title", "body", "depends_on"}
        if extra:
            fail(f"slice {i} has unknown keys: {sorted(extra)}")
        sid, title = item.get("id"), item.get("title")
        body, deps = item.get("body", ""), item.get("depends_on", [])
        if not isinstance(sid, str) or not SLICE_ID.fullmatch(sid) or sid in seen:
            fail(f"slice {i}: id must be a unique short slug (a-z, 0-9, -)")
        if not isinstance(title, str) or not title.strip() or len(title) > MAX_TITLE or "\n" in title:
            fail(f"slice {sid}: title must be one line of 1 to {MAX_TITLE} characters")
        if not isinstance(body, str) or len(body) > MAX_BODY:
            fail(f"slice {sid}: body must be a string of at most {MAX_BODY} characters")
        if not isinstance(deps, list) or any(d not in seen for d in deps) or len(set(deps)) != len(deps):
            fail(f"slice {sid}: depends_on must list ids of slices earlier in the list")
        seen.add(sid)
        # A forged marker in the body could not win (ours comes first), but keep bodies clean.
        out.append({"id": sid, "title": title.strip(), "body": body.replace("<!-- agent-slice", "<!-- "),
                    "depends_on": deps})
    return out


def epic_slices(api, repo, epic, owner, bot):
    """Every slice issue of this epic, open or closed, with its parsed marker."""
    issues = api.list(f"repos/{repo}/issues?labels={quote(route.SLICE_LABEL)}&state=all&per_page=100")
    found = []
    for issue in issues:
        if "pull_request" in issue:
            continue
        info = route.slice_info(issue, owner, bot)
        if info and info["epic"] == epic:
            found.append({**issue, "slice": info})
    return found


def start(api, repo, number):
    # Labeling with the App token is what starts the slice run (the caller allows this bot event).
    api.request("POST", f"repos/{repo}/issues/{number}/labels", {"labels": ["agent"]})


def comment(api, repo, number, body):
    api.request("POST", f"repos/{repo}/issues/{number}/comments", {"body": body})


def create(api, repo, epic, owner, bot, path=OUT / "slices.json"):
    if not path.is_file():
        print("no slices.json: nothing to create")
        return []
    try:
        slices = validate(json.loads(path.read_text(encoding="utf-8")))
    except (SystemExit, ValueError) as err:
        comment(api, repo, epic, f"The slice list was rejected, no issues were created: {err}\n\n"
                "Reply `@agent fix the slice list` to correct it.")
        raise SystemExit(f"slices.json rejected: {err}")
    if epic_slices(api, repo, epic, owner, bot):
        raise SystemExit(f"Epic #{epic} already has slice issues. Refusing to create more.")

    numbers, lines = {}, []
    for s in slices:
        deps = [numbers[d] for d in s["depends_on"]]
        body = (
            f"<!-- agent-slice epic={epic} id={s['id']} deps={','.join(map(str, deps))} -->\n"
            f"Slice `{s['id']}` of epic #{epic}. The design is under `docs/design/` on branch "
            f"`agent/issue-{epic}`.\n"
            f"Depends on: {', '.join(f'#{d}' for d in deps) or 'none'}\n\n{s['body']}"
        )
        labels = [route.SLICE_LABEL] + ([WAITING] if deps else [])
        created = api.request("POST", f"repos/{repo}/issues",
                              {"title": f"[#{epic}] {s['title']}", "body": body, "labels": labels})
        numbers[s["id"]] = created["number"]
        lines.append(f"- #{created['number']} `{s['id']}`: {s['title']}"
                     + (f" (after {', '.join(f'#{d}' for d in deps)})" if deps else " (starting now)"))
    for s in slices:
        if not s["depends_on"]:
            start(api, repo, numbers[s["id"]])
    comment(api, repo, epic,
            f"Created {len(slices)} slice issue(s). Each one runs on its own branch and its PR is merged "
            f"into `agent/issue-{epic}` when it finishes. Slices start as soon as their dependencies "
            "are merged.\n\n" + "\n".join(lines))
    return list(numbers.values())


def run_status(path=OUT / "state.md"):
    match = STATUS.search(path.read_text(encoding="utf-8")) if path.is_file() else None
    return match.group(1) if match else None


def land(api, repo, number, epic, pr, owner, bot, state_path=OUT / "state.md"):
    status = run_status(state_path)
    if status != "ready-for-review":
        print(f"slice #{number} status is {status!r}: not landing")
        return False
    if not pr:
        print(f"slice #{number} has no PR (no commits): not landing")
        return False
    epic_ref = f"agent/issue-{epic}"
    pull = api.get(f"repos/{repo}/pulls/{pr}")
    if pull.get("merged"):
        comment(api, repo, number,
                f"PR #{pr} was already merged into `{epic_ref}`, so this run's commits are not in the epic. "
                f"Ask for follow-up changes on the epic PR instead.")
        return False
    if pull["base"]["ref"] != epic_ref or pull["state"] != "open":
        raise SystemExit(f"PR #{pr} is not an open PR into {epic_ref}. Refusing to merge it.")
    try:
        merge(api, repo, pr, f"Merge slice #{number} into epic #{epic} (#{pr})")
    except GhError as err:
        comment(api, repo, number,
                f"Could not merge PR #{pr} into `{epic_ref}`: {err}\n\n"
                "If it conflicts with slices merged since, reply `@agent merge the epic branch and resolve "
                "the conflicts`.")
        raise SystemExit(1)
    api.request("PATCH", f"repos/{repo}/issues/{number}", {"state": "closed", "state_reason": "completed"})
    comment(api, repo, number, f"Merged into `{epic_ref}` with #{pr}.")
    start_ready(api, repo, epic, owner, bot, just_closed=number)
    return True


def merge(api, repo, pr, title):
    for attempt in range(MERGE_ATTEMPTS):
        try:
            return api.request("PUT", f"repos/{repo}/pulls/{pr}/merge", {"merge_method": "merge", "commit_title": title})
        except GhError:
            if attempt == MERGE_ATTEMPTS - 1:
                raise
            time.sleep(MERGE_RETRY_SECONDS)


def start_ready(api, repo, epic, owner, bot, just_closed=None):
    siblings = epic_slices(api, repo, epic, owner, bot)
    closed = {s["number"] for s in siblings if s["state"] == "closed"} | {just_closed}
    started = []
    for s in siblings:
        if s["state"] != "open" or WAITING not in route.label_names(s):
            continue
        if not all(d in closed for d in s["slice"]["deps"]):
            continue
        try:
            # Two slices landing at once: only the run whose delete succeeds starts the dependent.
            api.request("DELETE", f"repos/{repo}/issues/{s['number']}/labels/{quote(WAITING)}")
        except GhError:
            continue
        start(api, repo, s["number"])
        started.append(s["number"])
    if siblings and all(s["state"] == "closed" or s["number"] == just_closed for s in siblings):
        finish(api, repo, epic, len(siblings))
    return started


def finish(api, repo, epic, count):
    head = f"{repo.split('/')[0]}:agent/issue-{epic}"
    pulls = api.list(f"repos/{repo}/pulls?head={quote(head)}&state=open")
    if pulls and pulls[0].get("draft"):
        api.pr_ready(repo, pulls[0]["number"])
    where = f"the epic PR #{pulls[0]['number']}" if pulls else f"branch `agent/issue-{epic}` (no open PR found)"
    comment(api, repo, epic,
            f"All {count} slices are merged into `agent/issue-{epic}`. Review {where}: it holds the whole "
            "feature. Each slice PR is linked from its slice issue, for tracing back. Comment `@agent ...` "
            "on the epic PR for changes.")


def main():
    env = os.environ
    repo, bot = env["REPO"], env["AGENT_BOT_LOGIN"]
    owner = repo.split("/")[0]
    api = GhApi()
    if sys.argv[1:] == ["create"]:
        create(api, repo, int(env["ISSUE"]), owner, bot)
    elif sys.argv[1:] == ["land"]:
        land(api, repo, int(env["ISSUE"]), int(env["EPIC"]), env.get("PR", ""), owner, bot)
    else:
        raise SystemExit("usage: slices.py create|land")


if __name__ == "__main__":
    sys.exit(main())
