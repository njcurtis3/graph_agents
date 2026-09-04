#!/usr/bin/env python
"""Self-test for audit-fleet.py. Stdlib only, no pytest.

    python graph_agents/.graph/test_audit_fleet.py

Every case builds a COMPLETE synthetic umbrella in a temp directory -- its own fleet, its
own `CURRENT-STATE.md`, its own git repo with a controlled commit date, its own registered
app -- then changes exactly ONE claim and asks the script what drifted. Nothing here reads
the live fleet, so a concurrent session cannot make this test flap and this test cannot
disturb one.

The fixture is a whole umbrella rather than a stub because the tool's entire job is
comparing a document to a filesystem. A mocked filesystem would test the parser and skip
the comparison, which is the half that matters.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
FAILURES = []

DEFAULTS = {
    "verified": "2026-06-01",
    "commit_date": "2026-01-01T12:00:00",
    "status_runs": "two",
    "graph_ln": 3,
    "apps": 1,
    "agents": 2,
    "skills": 2,
    "alpha_ln": 2,
    "beta_ln": 2,
    "branch": "master",
    "remote": "github.com/example/testfleet",
    "hook_path": ".claude/hooks/alpha.py",
    "hook_ln": 1,
    "scout_model": "haiku",
    "scout_tools": "Read, Bash",
    "scout_ln": 6,
    "scout_exec": "yes, 1 run",
    "ops_ln": 6,
    "ops_exec": "**no**",
    # `runs` is what the doc's table LISTS; `run_states` is what exists on disk. They are
    # separate on purpose -- the drift this tool was built for is a run present in one and
    # absent from the other.
    "runs": (("run-one", "**executed**, approved"),
             ("run-two", "**parked** at the gate")),
    "run_states": {"run-one": ("done", True), "run-two": ("parked", False)},
}

DOC = """# CURRENT-STATE - testfleet

> **Last verified: %(verified)s**

## Status: %(status_runs)s runs, all of them executed

## What is live

| Thing | State | Path |
|---|---|---|
| Graph spec | live | `graph_agents/GRAPH.md` (%(graph_ln)d ln) |
| Portfolio index | live, **%(apps)d nodes** | `graph_agents/portfolio/registry.json` |
| %(agents)d agent nodes | live | `.claude/agents/` |
| %(skills)d skills | `alpha` exercised (%(alpha_ln)d ln); `beta` unused (%(beta_ln)d ln) | `.claude/skills/` |
| Fleet git repo | live, branch `%(branch)s`, remote `origin` at `%(remote)s` | `graph_agents/.git` |
| A hook | live | `%(hook_path)s` (%(hook_ln)d ln) |

### Node roster (frontmatter verified)

| Node | Model | Tools | Lines | Has executed? |
|---|---|---|---|---|
| `scout` | %(scout_model)s | %(scout_tools)s | %(scout_ln)d | %(scout_exec)s |
| `ops` | opus | Read, Bash | %(ops_ln)d | %(ops_exec)s |

## Runs

| Run | App | Shape | Status | Outcome |
|---|---|---|---|---|
%(run_rows)s

## Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-01-01 | a decision | because |
"""

AGENT = """---
name: %s
description: a node.
tools: %s
model: %s
---
"""


def check(label, got, want):
    if got == want:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s -- expected %r, got %r" % (label, want, got))
        FAILURES.append(label)


def write(path, text):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def git(repo, *args, **env):
    environ = dict(os.environ)
    environ.update(env)
    proc = subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True, env=environ)
    return proc.returncode, proc.stdout.strip()


def build(tmp, **over):
    """A whole synthetic umbrella. Returns the path to the copied audit-fleet.py."""
    opts = dict(DEFAULTS)
    opts.update(over)
    fleet = os.path.join(tmp, "graph_agents")
    graph = os.path.join(fleet, ".graph")

    for name in ("audit-fleet.py", "verify-state.py"):
        write(os.path.join(graph, name), "")
        shutil.copy(os.path.join(HERE, name), os.path.join(graph, name))
    write(os.path.join(graph, "runs", "_schema.json"), "")
    shutil.copy(os.path.join(HERE, "runs", "_schema.json"),
                os.path.join(graph, "runs", "_schema.json"))

    write(os.path.join(fleet, "GRAPH.md"), "a\nb\nc\n")
    write(os.path.join(fleet, ".gitignore"), "portfolio/registry.json\n__pycache__/\n")

    # -- nodes. `scout` has run in the fixture's history; `ops` never has.
    write(os.path.join(fleet, ".claude", "agents", "scout.md"),
          AGENT % ("scout", "Read, Bash", "haiku"))
    write(os.path.join(fleet, ".claude", "agents", "ops.md"),
          AGENT % ("ops", "Read, Bash", "opus"))
    for extra in opts.get("extra_agents", ()):
        write(os.path.join(fleet, ".claude", "agents", extra + ".md"),
              AGENT % (extra, "Read", "opus"))

    for skill in ("alpha", "beta"):
        write(os.path.join(fleet, ".claude", "skills", skill, "SKILL.md"), "a\nb\n")

    # -- hooks, and whatever settings.json is meant to claim about them
    write(os.path.join(fleet, ".claude", "hooks", "alpha.py"), "x\n")
    for extra in opts.get("extra_hooks", ()):
        write(os.path.join(fleet, ".claude", "hooks", extra + ".py"), "x\n")
    commands = list(opts.get("hook_commands", (".claude/hooks/alpha.py",)))
    write(os.path.join(fleet, ".claude", "settings.json"), json.dumps({"hooks": {
        "PostToolUse": [{"matcher": "*", "hooks": [
            {"type": "command",
             "command": "python \"${CLAUDE_PROJECT_DIR:-.}/graph_agents/%s\" || true" % c}
            for c in commands]}]}}))

    # -- the registry, and the one app it points at
    apps = opts.get("registry_apps", [{"id": "appone", "path": "appone",
                                       "entry_docs": ["appone/CLAUDE.md"]}])
    write(os.path.join(fleet, "portfolio", "registry.json"), json.dumps({"apps": apps}))
    if opts.get("make_app", True):
        app = os.path.join(tmp, "appone")
        write(os.path.join(app, "CLAUDE.md"), "app\n")
        if opts.get("app_is_repo", True):
            git(app, "init", "-q")

    # -- runs. A written `scout` key is what makes the node count as executed.
    for run_id, (status, executed) in opts["run_states"].items():
        state = {"run_id": run_id, "app": "appone", "status": status,
                 "approved_by_human": True, "log": ["opened"]}
        if executed:
            state["scout"] = {"written_by": "scout", "facts": ["a fact (f:1)"],
                              "unknowns": [], "risks": []}
        write(os.path.join(graph, "runs", run_id, "state.json"), json.dumps(state))

    rows = "\n".join("| `%s` | appone | single-loop | %s | outcome |" % (r[0], r[1])
                     for r in opts["runs"])
    opts["run_rows"] = rows
    write(os.path.join(fleet, "CURRENT-STATE.md"), DOC % opts)

    # -- history, with a controlled committer date so the freshness check is testable
    git(fleet, "init", "-q")
    git(fleet, "config", "user.email", "test@example.com")
    git(fleet, "config", "user.name", "test")
    git(fleet, "config", "commit.gpgsign", "false")
    git(fleet, "checkout", "-q", "-B", opts["branch"])
    git(fleet, "remote", "add", "origin",
        "https://%s.git" % opts.get("git_remote", opts["remote"]))
    add = ["add", "-A"] + (["-f", "portfolio/registry.json"]
                           if opts.get("track_registry") else [])
    git(fleet, *add)
    git(fleet, "commit", "-qm", "fixture",
        GIT_AUTHOR_DATE=opts["commit_date"], GIT_COMMITTER_DATE=opts["commit_date"])
    return os.path.join(graph, "audit-fleet.py")


def run(script, *args):
    proc = subprocess.run([sys.executable, script] + list(args),
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def case(label, expect_clean, expect_text=None, args=(), **over):
    tmp = tempfile.mkdtemp(prefix="auditfleet-")
    try:
        script = build(tmp, **over)
        code, out = run(script, *args)
        check(label, code == 0, expect_clean)
        if expect_text is not None:
            if expect_text not in out:
                print("  FAIL %s -- missing %r in:\n%s" % (label, expect_text, out))
                FAILURES.append(label + " (text)")
            else:
                print("  ok   %s :: %s" % (label, expect_text))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


print("audit-fleet.py")

# -- the baseline. Everything the fixture claims is true, so nothing may be reported.
case("a fleet whose doc matches disk is clean", True, "none drifted")
case("-v lists the claims it checked", True, "ok   `scout` runs on haiku", args=("-v",))

# -- line counts, the most common drift and the reason this exists
case("BLOCKS on a wrong line count", False, "disk has 3", graph_ln=9)
case("BLOCKS on a claim naming a file that is gone", False, "no such file on disk",
     hook_path=".claude/hooks/deleted.py")
case("BLOCKS on a wrong skill line count", False, "skill `beta` is 7 ln", beta_ln=7)
case("resolves a fleet-relative path as written", True, hook_path=".claude/hooks/alpha.py")

# -- the roster: four independent claims per row
case("BLOCKS on a wrong roster line count", False, "`scout.md` is 9 ln", scout_ln=9)
case("BLOCKS on a wrong model tier", False, "frontmatter says 'haiku'",
     scout_model="opus")
case("BLOCKS on a wrong tool grant", False, "frontmatter grants Read, Bash",
     scout_tools="Read, Write, Bash")
case("BLOCKS when a node that HAS run is recorded as never having run", False,
     "`scout` has never executed", scout_exec="**no**")
case("reads execution from state.json, not from the heartbeat", True,
     "executed: scout 1", args=("-v",))
case("BLOCKS when a node that never ran is recorded as having run", False,
     "`ops` has executed", ops_exec="yes, 3 runs")

# -- counts
case("BLOCKS on a wrong agent-node count", False, "2 .md files", agents=3)
case("BLOCKS on a wrong skill count", False, "2 SKILL.md files", skills=5)
case("BLOCKS on a wrong portfolio count", False, "registry.json has 1 apps", apps=4)
case("counts the agents actually on disk", False, "3 .md files in .claude/agents/",
     extra_agents=("builder",))

# -- the registry against disk
case("BLOCKS when a registered app has no directory", False, "no such directory",
     make_app=False)
case("BLOCKS when an entry doc is missing", False, "entry doc missing",
     registry_apps=[{"id": "appone", "path": "appone",
                     "entry_docs": ["appone/README.md"]}])
case("BLOCKS when a registered app is not its own git repo", False,
     "the constitution says every app has one", app_is_repo=False)
case("BLOCKS when the registry becomes tracked by git", False,
     "it is now tracked by git", track_registry=True)

# -- runs
case("BLOCKS when the table lists a run that does not exist", False,
     "no such run directory",
     runs=(("run-one", "**executed**"), ("ghost", "**executed**")),
     run_states={"run-one": ("done", True)}, status_runs="one")
case("BLOCKS when a CLOSED run is missing from the table", False,
     "closed run `run-three` is in the Runs table", status_runs="three",
     run_states={"run-one": ("done", True), "run-two": ("parked", False),
                 "run-three": ("done", True)})
case("an IN-FLIGHT run missing from the table is a note, not drift", True,
     "in flight, not drift", status_runs="three",
     run_states={"run-one": ("done", True), "run-two": ("parked", False),
                 "run-three": ("building", False)})
case("BLOCKS when the table contradicts the run's own status", False,
     "state.json says 'parked'",
     runs=(("run-one", "**executed**"), ("run-two", "**executed**")))
case("`done` reading as \"executed\" in that table's prose is not drift", True)
case("BLOCKS on a wrong run count in the status headline", False,
     "2 run directories on disk", status_runs="nine")

# -- the fleet repo's own row. The branch half is below: the fixture creates the branch it
# claims, so disagreeing with itself takes a rename after the fact.
case("BLOCKS on a wrong remote", False, "origin is",
     git_remote="github.com/example/somewhere-else")

# -- hooks
case("BLOCKS when a registered hook is not on disk", False,
     "names a script that is not on disk",
     hook_commands=(".claude/hooks/alpha.py", ".claude/hooks/ghost.py"))
case("BLOCKS on a hook file nothing registers", False, "no settings.json entry runs it",
     extra_hooks=("orphan",))

# -- the stamp
case("BLOCKS when a definition file was committed after the stamp", False,
     "changed after 2026-01-01", verified="2026-01-01", commit_date="2026-06-01T12:00:00")
case("BLOCKS when there is no `Last verified:` stamp at all", False, "none found",
     verified="")

print()

# The branch case above is a trap: `branch` names the branch the fixture CREATES, so it can
# never disagree with itself. Prove the check works by renaming the branch after the fact.
tmp = tempfile.mkdtemp(prefix="auditfleet-")
try:
    script = build(tmp)
    git(os.path.join(tmp, "graph_agents"), "branch", "-m", "master", "elsewhere")
    code, out = run(script)
    check("BLOCKS when the fleet is not on the branch the doc claims", code == 0, False)
    check("and names the branch git actually reports",
          "git says 'elsewhere'" in out, True)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# It never writes. The whole point of the `Last verified:` decision is that a script must
# not discharge an obligation it cannot actually satisfy.
tmp = tempfile.mkdtemp(prefix="auditfleet-")
try:
    script = build(tmp, graph_ln=9)
    before = {}
    for root, _, files in os.walk(os.path.join(tmp, "graph_agents")):
        if ".git" in root:
            continue
        for name in files:
            path = os.path.join(root, name)
            with open(path, "rb") as fh:
                before[path] = fh.read()
    run(script)
    after = {}
    for path in before:
        with open(path, "rb") as fh:
            after[path] = fh.read()
    check("it never writes -- every fleet file is byte-identical after a run",
          after == before, True)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
if FAILURES:
    print("%d FAILED" % len(FAILURES))
    for line in FAILURES:
        print("  - %s" % line)
    sys.exit(1)
print("all checks passed")
