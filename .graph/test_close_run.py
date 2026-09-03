#!/usr/bin/env python
"""Self-test for close-run.py. Stdlib only, no pytest.

    python graph_agents/.graph/test_close_run.py

The whole value of `close-run.py` is one check nothing else in the fleet makes: that the
work is in git, not merely that `state.json` says it passed. A test that stubbed git
would test everything except that. So this builds a **real repository** per case --
`git init`, a baseline commit, a branch with work on it, merged or not -- and asks the
script the question for real.

Every case runs against a COPIED fleet in a temp directory: its own `.graph`, its own
`portfolio/registry.json`, its own target repo. Nothing here can touch the live
`.graph/CURRENT`, which the scope guard reads and a concurrent session may be using.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
FAILURES = []


def check(label, got, want):
    if got == want:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s -- expected %r, got %r" % (label, want, got))
        FAILURES.append(label)


def git(repo, *args):
    proc = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip()


def make_repo(path, branch_work="feature-x", merge=True):
    """A repo with a baseline commit and, optionally, a merged feature branch.

    Returns the branch's tip sha, so a case can delete the branch and still name the
    commit -- the fallback that keeps a run verifiable after normal branch hygiene.
    """
    os.makedirs(path, exist_ok=True)
    git(path, "init", "-q")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "test")
    git(path, "config", "commit.gpgsign", "false")
    with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("base\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "baseline")
    _, main = git(path, "symbolic-ref", "--short", "HEAD")
    if not branch_work:
        return main, None
    git(path, "checkout", "-qb", branch_work)
    with open(os.path.join(path, "work.txt"), "w", encoding="utf-8") as fh:
        fh.write("slice work\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "slice work")
    _, sha = git(path, "rev-parse", "HEAD")
    git(path, "checkout", "-q", main)
    if merge:
        git(path, "merge", "-q", "--no-ff", "-m", "merge", branch_work)
    return main, sha


def state_for(branch, verdict="PASS", built=True, reviewed=True, approved=True,
              status="reviewing", extra_slice=None, commit=None):
    state = {
        "run_id": "close-self-test",
        "goal": "a test run",
        "app": "targetapp",
        "status": status,
        "approved_by_human": approved,
        "scout": {"written_by": "scout", "facts": ["f (a:1)"], "unknowns": [], "risks": []},
        "architect": {"written_by": "architect", "shape": "single-loop",
                      "parallel_safe": False, "rationale": "r",
                      "plan": [{"slice": "s1", "intent": "i", "files": ["a"],
                                "done_when": "x"}]},
        "builders": {}, "reviews": {},
        "log": ["orchestrator: opened"],
    }
    if built:
        entry = {"written_by": "builder", "status": "done", "branch": branch or "",
                 "changed": ["a"], "notes": "", "gate_results": "cmd -> ok"}
        if commit:
            entry["commit"] = commit
        state["builders"]["s1"] = entry
    if reviewed:
        state["reviews"]["s1"] = {"written_by": "reviewer", "verdict": verdict,
                                  "attempt": 1, "summary": "s", "findings": []}
    if extra_slice:
        state["builders"][extra_slice] = {"written_by": "builder", "status": "done",
                                          "branch": branch or "", "changed": ["b"],
                                          "notes": "", "gate_results": "cmd -> ok"}
    return state


def build_fleet(tmp, state, make_target=True, **repo_kwargs):
    """A minimal umbrella: graph_agents/{.graph,portfolio} plus the target app repo."""
    fleet = os.path.join(tmp, "graph_agents")
    graph = os.path.join(fleet, ".graph")
    runs = os.path.join(graph, "runs")
    os.makedirs(os.path.join(runs, "a-run"))
    os.makedirs(os.path.join(fleet, "portfolio"))
    for name in ("close-run.py", "verify-state.py"):
        shutil.copy(os.path.join(HERE, name), os.path.join(graph, name))
    shutil.copy(os.path.join(HERE, "runs", "_schema.json"), os.path.join(runs, "_schema.json"))
    with open(os.path.join(fleet, "portfolio", "registry.json"), "w", encoding="utf-8") as fh:
        json.dump({"apps": [{"id": "targetapp", "path": "targetapp"}]}, fh)
    with open(os.path.join(runs, "a-run", "state.json"), "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    target = os.path.join(tmp, "targetapp")
    result = (None, None)
    if make_target:
        result = make_repo(target, **repo_kwargs)
    else:
        os.makedirs(target)
    return os.path.join(graph, "close-run.py"), result


def run_close(script, *args):
    proc = subprocess.run([sys.executable, script] + list(args),
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def case(label, state, expect_ok, expect_text=None, args=("a-run",), **fleet_kwargs):
    tmp = tempfile.mkdtemp(prefix="closetest-")
    try:
        script, _ = build_fleet(tmp, state, **fleet_kwargs)
        code, out = run_close(script, *args)
        check(label, code == 0, expect_ok)
        if expect_text is not None:
            if expect_text not in out:
                print("  FAIL %s -- missing %r in:\n%s" % (label, expect_text, out))
                FAILURES.append(label + " (text)")
            else:
                print("  ok   %s :: %s" % (label, expect_text))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


print("close-run.py")

# -- the happy path, and the merge proof that is the point of this script
case("closeable when the branch is merged", state_for("feature-x"), True, "closeable")
case("BLOCKS when the branch never landed", state_for("feature-x"), False,
     "NOT an ancestor", merge=False)

# -- everything the state file alone can be wrong about
case("BLOCKS on a REJECT verdict", state_for("feature-x", verdict="REJECT"), False,
     "is REJECT, not PASS")
case("BLOCKS on a slice with no review", state_for("feature-x", reviewed=False), False,
     "has no review")
case("BLOCKS on a slice never built", state_for("feature-x", built=False), False,
     "was never built")
case("BLOCKS before the human gate", state_for("feature-x", approved=False), False,
     "approved_by_human is not true")
case("BLOCKS on an off-plan slice with no reviewer",
     state_for("feature-x", extra_slice="closing_fix"), False, "(off-plan)")

# -- already closed
case("BLOCKS a run already done", state_for("feature-x", status="done"), False,
     "already `status: done`")
case("--recheck audits a closed run anyway", state_for("feature-x", status="done"), True,
     "closeable", args=("--recheck", "a-run"))

# -- the shapes that are fine and must not be reported as failures
case("direct commit to the main branch is not a merge failure",
     state_for("master"), True, "committed directly", branch_work="master")
case("no branch recorded is degraded mode, not a blocker",
     state_for(""), True, "nothing to merge")
case("a non-git target is degraded mode, not a blocker",
     state_for("feature-x"), True, "not a git repo", make_target=False)

# A branch deleted after merging is normal hygiene, so the run stays verifiable through
# the commit the builder recorded. Built by hand: the sha is not known until the repo is.
tmp = tempfile.mkdtemp(prefix="closetest-")
try:
    script, (main, sha) = build_fleet(tmp, state_for("feature-x"))
    git(os.path.join(tmp, "targetapp"), "branch", "-D", "feature-x")
    runs = os.path.join(tmp, "graph_agents", ".graph", "runs", "a-run", "state.json")
    with open(runs, "w", encoding="utf-8") as fh:
        json.dump(state_for("", commit="%s slice work" % sha), fh)
    code, out = run_close(script, "a-run")
    check("a deleted branch falls back to the recorded commit", code == 0, True)
    check("and says so", "commit %s is in %s" % (sha, main) in out, True)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# -- argument handling
case("exits 1 on an unknown run", state_for("feature-x"), False, args=("no-such-run",))

print()
if FAILURES:
    print("%d FAILED" % len(FAILURES))
    for line in FAILURES:
        print("  - %s" % line)
    sys.exit(1)
print("all checks passed")
