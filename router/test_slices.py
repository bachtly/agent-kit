import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slices  # noqa: E402

OWNER = "owner"
BOT = "agent-kit-bot[bot]"
REPO = f"{OWNER}/app"
SLICE_LIST = f"repos/{REPO}/issues?labels=type%3Aslice&state=all&per_page=100"


def slice_issue(number, sid, deps=(), state="open", labels=("type:slice",), epic=10, author=BOT):
    return {
        "number": number, "state": state, "user": {"login": author},
        "labels": [{"name": n} for n in labels],
        "body": f"<!-- agent-slice epic={epic} id={sid} deps={','.join(map(str, deps))} -->\nx",
    }


class FakeApi:
    """Records writes. `issues` is the slice issue list; created issues are appended to it."""

    def __init__(self, issues=(), pulls=None, fail=()):
        self.issues = list(issues)
        self.pulls = pulls or {}
        self.fail = set(fail)
        self.calls = []
        self.ready = []

    def get(self, path):
        return self.pulls[path]

    def list(self, path):
        if path == SLICE_LIST:
            return self.issues
        if path.startswith(f"repos/{REPO}/pulls?head="):
            return [{"number": 50, "draft": True}]
        raise KeyError(path)

    def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        if (method, path) in self.fail:
            raise slices.GhError("HTTP 409: conflict")
        if method == "POST" and path == f"repos/{REPO}/issues":
            number = 11 + sum(1 for m, p, _ in self.calls if (m, p) == (method, path)) - 1
            self.issues.append({"number": number, "state": "open", "user": {"login": BOT},
                                "labels": [{"name": n} for n in body["labels"]], "body": body["body"]})
            return {"number": number}
        if method == "PATCH":
            number = int(path.rsplit("/", 1)[1])
            for issue in self.issues:
                if issue["number"] == number:
                    issue["state"] = body["state"]
        return None

    def pr_ready(self, repo, number):
        self.ready.append(number)

    def labeled_agent(self):
        return [int(p.split("/")[-2]) for m, p, b in self.calls
                if m == "POST" and p.endswith("/labels") and b == {"labels": ["agent"]}]

    def comments(self, number):
        return [b["body"] for m, p, b in self.calls if m == "POST" and p == f"repos/{REPO}/issues/{number}/comments"]


def write(tmp, name, text):
    path = Path(tmp) / name
    path.write_text(text, encoding="utf-8")
    return path


GOOD = [
    {"id": "contract", "title": "Types", "depends_on": [], "body": "Goal"},
    {"id": "api", "title": "API", "depends_on": ["contract"], "body": "<!-- agent-slice epic=1 id=x deps= -->"},
    {"id": "ui", "title": "UI", "depends_on": []},
]


class ValidateTests(unittest.TestCase):
    def test_good_list_normalised(self):
        out = slices.validate(GOOD)
        self.assertEqual([s["id"] for s in out], ["contract", "api", "ui"])
        self.assertEqual(out[2]["body"], "")
        self.assertNotIn("<!-- agent-slice", out[1]["body"])

    def test_rejects(self):
        bad = {
            "not a list": {"id": "a"},
            "empty": [],
            "too many": [{"id": f"s{i}", "title": "t"} for i in range(slices.MAX_SLICES + 1)],
            "unknown key": [{"id": "a", "title": "t", "labels": ["agent"]}],
            "bad id": [{"id": "A B", "title": "t"}],
            "duplicate id": [{"id": "a", "title": "t"}, {"id": "a", "title": "t"}],
            "multiline title": [{"id": "a", "title": "t\nu"}],
            "long title": [{"id": "a", "title": "t" * 200}],
            "forward dep": [{"id": "a", "title": "t", "depends_on": ["b"]}, {"id": "b", "title": "t"}],
            "self dep": [{"id": "a", "title": "t", "depends_on": ["a"]}],
            "long body": [{"id": "a", "title": "t", "body": "x" * (slices.MAX_BODY + 1)}],
        }
        for name, data in bad.items():
            with self.assertRaises(SystemExit, msg=name):
                slices.validate(data)


class CreateTests(unittest.TestCase):
    def test_creates_marks_and_starts_independent_slices(self):
        api = FakeApi()
        with tempfile.TemporaryDirectory() as d:
            numbers = slices.create(api, REPO, 10, OWNER, BOT, write(d, "s.json", json.dumps(GOOD)))
        self.assertEqual(numbers, [11, 12, 13])
        api_issue = api.issues[1]
        self.assertTrue(api_issue["body"].startswith("<!-- agent-slice epic=10 id=api deps=11 -->\n"))
        self.assertEqual([lbl["name"] for lbl in api_issue["labels"]], ["type:slice", "slice:waiting"])
        self.assertEqual(api.labeled_agent(), [11, 13])
        self.assertIn("#12 `api`: API (after #11)", api.comments(10)[0])

    def test_no_file_is_a_no_op(self):
        api = FakeApi()
        self.assertEqual(slices.create(api, REPO, 10, OWNER, BOT, Path("missing.json")), [])
        self.assertEqual(api.calls, [])

    def test_refuses_second_breakdown(self):
        api = FakeApi(issues=[slice_issue(11, "contract")])
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                slices.create(api, REPO, 10, OWNER, BOT, write(d, "s.json", json.dumps(GOOD)))
        self.assertEqual(api.calls, [])

    def test_other_epics_and_foreign_issues_ignored(self):
        api = FakeApi(issues=[slice_issue(5, "a", epic=9), slice_issue(6, "b", author="stranger")])
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(len(slices.create(api, REPO, 10, OWNER, BOT, write(d, "s.json", json.dumps(GOOD)))), 3)


class LandTests(unittest.TestCase):
    PULL = {f"repos/{REPO}/pulls/30": {"merged": False, "state": "open", "base": {"ref": "agent/issue-10"}}}

    def land(self, api, status="ready-for-review", pr="30"):
        with tempfile.TemporaryDirectory() as d:
            state = write(d, "state.md", f"## Agent state\n\n**Status:** {status}\n")
            return slices.land(api, REPO, 11, 10, pr, OWNER, BOT, state)

    def test_merges_closes_and_starts_ready_dependents(self):
        api = FakeApi(issues=[
            slice_issue(11, "contract"),
            slice_issue(12, "api", deps=[11], labels=("type:slice", "slice:waiting")),
            slice_issue(13, "ui", deps=[11, 14], labels=("type:slice", "slice:waiting")),
            slice_issue(14, "db"),
        ], pulls=self.PULL)
        self.assertTrue(self.land(api))
        self.assertEqual(api.calls[0][:2], ("PUT", f"repos/{REPO}/pulls/30/merge"))
        self.assertEqual(api.calls[0][2]["merge_method"], "merge")
        self.assertIn(("PATCH", f"repos/{REPO}/issues/11", {"state": "closed", "state_reason": "completed"}),
                      api.calls)
        self.assertEqual(api.labeled_agent(), [12])
        self.assertEqual(api.ready, [])

    def test_not_landed_unless_ready_for_review(self):
        for status in ("in-progress", "blocked", "waiting-for-owner"):
            api = FakeApi(pulls=self.PULL)
            self.assertFalse(self.land(api, status=status))
            self.assertEqual(api.calls, [])

    def test_no_pr_not_landed(self):
        api = FakeApi()
        self.assertFalse(self.land(api, pr=""))

    def test_wrong_base_refused(self):
        api = FakeApi(pulls={f"repos/{REPO}/pulls/30": {"merged": False, "state": "open", "base": {"ref": "main"}}})
        with self.assertRaises(SystemExit):
            self.land(api)
        self.assertEqual(api.calls, [])

    def test_merge_conflict_reported_and_fails(self):
        api = FakeApi(issues=[slice_issue(11, "contract")], pulls=self.PULL,
                      fail={("PUT", f"repos/{REPO}/pulls/30/merge")})
        with self.assertRaises(SystemExit):
            self.land(api)
        self.assertIn("resolve", api.comments(11)[0])
        self.assertFalse(any(m == "PATCH" for m, _, _ in api.calls))

    def test_dependent_already_claimed_by_another_run_not_started_twice(self):
        api = FakeApi(issues=[
            slice_issue(11, "contract"),
            slice_issue(12, "api", deps=[11], labels=("type:slice", "slice:waiting")),
        ], pulls=self.PULL, fail={("DELETE", f"repos/{REPO}/issues/12/labels/slice%3Awaiting")})
        self.land(api)
        self.assertEqual(api.labeled_agent(), [])

    def test_last_slice_marks_epic_pr_ready(self):
        api = FakeApi(issues=[slice_issue(11, "contract"), slice_issue(12, "api", deps=[11], state="closed")],
                      pulls=self.PULL)
        self.land(api)
        self.assertEqual(api.ready, [50])
        self.assertIn("Review the epic PR #50", api.comments(10)[0])

    def test_already_merged_pr_explained(self):
        api = FakeApi(pulls={f"repos/{REPO}/pulls/30": {"merged": True, "state": "closed",
                                                       "base": {"ref": "agent/issue-10"}}})
        self.assertFalse(self.land(api))
        self.assertIn("already merged", api.comments(11)[0])


if __name__ == "__main__":
    unittest.main()
