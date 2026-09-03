#!/usr/bin/env python
"""Self-test for show-board.py. Stdlib only, no pytest.

    python graph_agents/.claude/hooks/test_show_board.py

This hook's whole contract is a shape: `{"systemMessage": ...}` on stdout for exactly one
event, and total silence for every other. Both halves matter. A board that fails to print
is a cosmetic loss; a board that prints on the wrong event, or crashes, costs a tool call
in every run forever.

**It runs against a COPIED fleet in a temp directory, not this one.** The existing hook
tests point the real `.graph/CURRENT` at a temp run and restore it afterwards, which is
fine when one session owns the repo and is a hazard the moment two do -- that pointer is
how `guard-builder-scope.py` finds the run it is protecting, so borrowing it for a
millisecond can misdirect a concurrent session's scope guard. A copy costs four files and
removes the shared state entirely.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
FLEET = os.path.normpath(os.path.join(HERE, "..", ".."))

FAILURES = []


def check(label, got, want):
    if got == want:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s -- expected %r, got %r" % (label, want, got))
        FAILURES.append(label)


def build_fleet(tmp, state, current="a-run"):
    """A minimal copy of the fleet: the hook, brief.py, verify-state.py, one run."""
    graph = os.path.join(tmp, ".graph")
    hooks = os.path.join(tmp, ".claude", "hooks")
    runs = os.path.join(graph, "runs")
    os.makedirs(hooks)
    os.makedirs(os.path.join(runs, "a-run"))
    for name in ("brief.py", "verify-state.py"):
        shutil.copy(os.path.join(FLEET, ".graph", name), os.path.join(graph, name))
    shutil.copy(os.path.join(FLEET, ".graph", "runs", "_schema.json"),
                os.path.join(runs, "_schema.json"))
    shutil.copy(os.path.join(HERE, "show-board.py"), os.path.join(hooks, "show-board.py"))
    if state is not None:
        with open(os.path.join(runs, "a-run", "state.json"), "w", encoding="utf-8") as fh:
            json.dump(state, fh)
    if current is not None:
        with open(os.path.join(graph, "CURRENT"), "w", encoding="utf-8") as fh:
            fh.write(current)
    return os.path.join(hooks, "show-board.py")


def run_hook(hook, payload, cwd=None):
    """(stdout, exit code). Mirrors how Claude Code invokes the hook."""
    proc = subprocess.run(
        [sys.executable, hook],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True, text=True, cwd=cwd,
    )
    if proc.returncode != 0:
        FAILURES.append("hook exited %d, stderr: %s" % (proc.returncode, proc.stderr[:400]))
    return proc.stdout, proc.returncode


IN_FLIGHT = {
    "run_id": "board-self-test",
    "goal": "prove the board renders from a hook",
    "app": "huntstack",
    "status": "building",
    "approved_by_human": True,
    "scout": {"written_by": "scout", "facts": ["a (f.ts:1)"], "unknowns": [], "risks": []},
    "architect": {"written_by": "architect", "shape": "diamond", "parallel_safe": True,
                  "rationale": "r",
                  "plan": [{"slice": "s1", "intent": "i", "files": ["a"], "done_when": "x"},
                           {"slice": "s2", "intent": "i", "files": ["b"], "done_when": "x"}]},
    "builders": {"s1": {"written_by": "builder", "status": "done", "branch": "s1",
                        "changed": ["a"], "notes": ""}},
    "reviews": {},
}

AGENT_RETURN = {"hook_event_name": "PostToolUse", "tool_name": "Agent",
                "tool_input": {"subagent_type": "builder"}, "tool_response": {}}


def silent(label, payload, state=IN_FLIGHT, current="a-run"):
    tmp = tempfile.mkdtemp(prefix="boardtest-")
    try:
        hook = build_fleet(tmp, state, current)
        out, _ = run_hook(hook, payload)
        check(label, out, "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


print("show-board.py")

# -- the one case it must fire on
tmp = tempfile.mkdtemp(prefix="boardtest-")
try:
    hook = build_fleet(tmp, IN_FLIGHT)
    out, code = run_hook(hook, AGENT_RETURN)
    check("exits 0 on the happy path", code, 0)
    check("stdout is parseable as JSON", bool(out) and out.strip()[:1] == "{"
          and out.strip()[-1:] == "}", True)
    try:
        parsed = json.loads(out)
    except ValueError:
        parsed = {}
        FAILURES.append("stdout did not parse as JSON: %r" % out[:200])
    check("carries systemMessage", "systemMessage" in parsed, True)
    check("carries nothing else", sorted(parsed), ["systemMessage"])

    message = parsed.get("systemMessage", "")
    check("names the run", "board-self-test" in message, True)
    check("shows the gate", "gate ok" in message, True)
    check("shows the built slice", "s1" in message and "build done" in message, True)
    check("shows the unstarted slice", "s2         build --" in message, True)
    check("is ASCII only", all(ord(c) < 128 for c in message), True)
    check("is a board, not a transcript", len(message.splitlines()) <= 15, True)

    # cwd independence -- gap #18's lesson, applied before it can bite this one.
    out_elsewhere, _ = run_hook(hook, AGENT_RETURN, cwd=os.path.dirname(tmp))
    check("identical from another cwd", out_elsewhere, out)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# -- everything it must stay silent on
silent("silent on a non-Agent tool",
       dict(AGENT_RETURN, tool_name="Bash"))
silent("silent on PreToolUse",
       dict(AGENT_RETURN, hook_event_name="PreToolUse"))
silent("silent on SubagentStop",
       dict(AGENT_RETURN, hook_event_name="SubagentStop"))
silent("silent when a subagent is the caller",
       dict(AGENT_RETURN, agent_type="builder"))
silent("silent with no CURRENT pointer", AGENT_RETURN, current=None)
silent("silent on an empty CURRENT pointer", AGENT_RETURN, current="")
silent("silent when CURRENT names a missing run", AGENT_RETURN, current="no-such-run")
silent("silent with no state.json", AGENT_RETURN, state=None)
silent("silent on a closed run", AGENT_RETURN, state=dict(IN_FLIGHT, status="done"))
silent("silent on a blocked run", AGENT_RETURN, state=dict(IN_FLIGHT, status="blocked"))
silent("silent on malformed stdin", "not json at all")
silent("silent on empty stdin", "")
silent("silent on a JSON array", "[1,2,3]")
silent("silent on a state.json that is not an object", AGENT_RETURN, state=["nope"])

print()
if FAILURES:
    print("%d FAILED" % len(FAILURES))
    for line in FAILURES:
        print("  - %s" % line)
    sys.exit(1)
print("all checks passed")
