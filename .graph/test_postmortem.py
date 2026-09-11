#!/usr/bin/env python
"""Self-test for postmortem.py. Stdlib only, no pytest.

    python graph_agents/.graph/test_postmortem.py

The one thing this script must never get wrong is gap #20: a phantom `stop` (fresh id,
no matching `start` or `tool` event) must never be counted as a lane, and nothing here
may read a `stop` timestamp as a boundary. Every case below is built with that pollution
mixed in on purpose, the way real `activity.jsonl` files carry it, rather than testing
against a clean log no real run has.

Runs against a COPIED fleet in a temp directory -- its own `.graph/runs/<id>/` -- so
nothing here touches the live `.graph/CURRENT` a concurrent session may hold.
"""
import json
import os
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


def state_for(plan, builders, reviews, shape="single-loop", app="umbrella"):
    return {
        "run_id": "t", "goal": "test", "app": app, "status": "done",
        "scout": {"written_by": "scout", "facts": ["f"], "unknowns": [], "risks": []},
        "architect": {"written_by": "architect", "plan": plan, "shape": shape,
                      "parallel_safe": shape == "diamond", "rationale": "test"},
        "approved_by_human": True,
        "builders": builders,
        "reviews": reviews,
        "integrator": {}, "ops": {}, "log": [],
    }


def write_run(root, run_id, state, events):
    run_dir = os.path.join(root, ".graph", "runs", run_id)
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "state.json"), "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    if events is not None:
        with open(os.path.join(run_dir, "activity.jsonl"), "w", encoding="utf-8") as fh:
            for event in events:
                fh.write(json.dumps(event) + "\n")
    return run_dir


def run(root, run_id):
    script = os.path.join(root, ".graph", "postmortem.py")
    proc = subprocess.run([sys.executable, script, run_id], cwd=root,
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout


def fresh_fleet():
    """A `.graph/` with the real verify-state.py + _schema.json, else the import breaks."""
    tmp = tempfile.mkdtemp(prefix="postmortem-test-")
    graph_dir = os.path.join(tmp, ".graph")
    os.makedirs(graph_dir, exist_ok=True)
    for name in ("verify-state.py", "postmortem.py"):
        src = os.path.join(HERE, name)
        with open(src, encoding="utf-8") as fh:
            content = fh.read()
        with open(os.path.join(graph_dir, name), "w", encoding="utf-8") as fh:
            fh.write(content)
    os.makedirs(os.path.join(graph_dir, "runs"), exist_ok=True)
    schema_src = os.path.join(HERE, "runs", "_schema.json")
    with open(schema_src, encoding="utf-8") as fh:
        schema = fh.read()
    with open(os.path.join(graph_dir, "runs", "_schema.json"), "w", encoding="utf-8") as fh:
        fh.write(schema)
    return tmp


def ev(t, agent, id_=None, kind="tool", tool=None):
    e = {"t": t, "ev": kind, "agent": agent}
    if id_ is not None:
        e["id"] = id_
    if tool is not None:
        e["tool"] = tool
    return e


def main():
    root = fresh_fleet()
    script = os.path.join(root, ".graph", "postmortem.py")

    # -- case 1: phantom stops (fresh id, only a `stop`) are excluded from tool activity,
    #    and counted, never folded into a real lane.
    plan = [{"slice": "s1", "intent": "", "files": [], "done_when": ""}]
    builders = {"s1": {"written_by": "builder", "status": "done", "branch": "b1",
                       "changed": [], "notes": ""}}
    reviews = {"s1": {"written_by": "reviewer", "verdict": "PASS", "attempt": 1,
                      "summary": "", "findings": []}}
    state = state_for(plan, builders, reviews)
    events = [
        ev(1.0, "scout", "s-1", "start"),
        ev(2.0, "scout", "s-1", "tool", "Read"),
        ev(3.0, "scout", "s-1", "stop"),
        # three phantom stops: fresh ids, no start, no tool -- gap #20's exact shape.
        ev(2.5, "orchestrator", "phantom-1", "stop"),
        ev(2.6, "orchestrator", "phantom-2", "stop"),
        ev(2.7, "orchestrator", "phantom-3", "stop"),
    ]
    write_run(root, "r1", state, events)
    code, out = run(root, "r1")
    check("case1 exit code", code, 0)
    check("case1 phantom count reported", "3 phantom stop event(s) excluded" in out, True)
    check("case1 scout lane counted once", "scout        1 lane(s), 1 tool call(s)" in out, True)
    check("case1 no orchestrator lane from phantoms",
          "orchestrator 1 lane" in out or "orchestrator 2 lane" in out
          or "orchestrator 3 lane" in out, False)

    # -- case 2: two builder lanes in a diamond whose tool-bounded windows overlap.
    plan2 = [{"slice": "s1", "intent": "", "files": [], "done_when": "", "risk": "high"},
             {"slice": "s2", "intent": "", "files": [], "done_when": "", "risk": "low"}]
    builders2 = {
        "s1": {"written_by": "builder", "status": "done", "branch": "b1", "changed": [], "notes": ""},
        "s2": {"written_by": "builder", "status": "done", "branch": "b2", "changed": [], "notes": ""},
    }
    reviews2 = {
        "s1": {"written_by": "reviewer", "verdict": "REJECT", "attempt": 1, "summary": "", "findings": [],
               "attempt_2": {"written_by": "reviewer", "verdict": "PASS", "attempt": 2, "summary": "", "findings": []}},
        "s2": {"written_by": "reviewer", "verdict": "PASS", "attempt": 1, "summary": "", "findings": []},
    }
    state2 = state_for(plan2, builders2, reviews2, shape="diamond")
    events2 = [
        ev(10.0, "builder", "b-1", "start"),
        ev(11.0, "builder", "b-1", "tool", "Edit"),
        ev(15.0, "builder", "b-1", "tool", "Bash"),
        ev(10.5, "builder", "b-2", "start"),
        ev(12.0, "builder", "b-2", "tool", "Edit"),
    ]
    write_run(root, "r2", state2, events2)
    code, out = run(root, "r2")
    check("case2 exit code", code, 0)
    check("case2 overlap detected", "1/1 pair(s) overlap" in out, True)
    check("case2 genuinely concurrent", "genuinely concurrent" in out, True)
    check("case2 s1 looped", "s1     risk=high  PASS, attempt 2 (looped)" in out, True)
    check("case2 s2 not looped", "s2     risk=low   PASS, attempt 1" in out, True)
    check("case2 high-risk earning its cost note",
          "high-risk slices are where the loops are" in out, True)

    # -- case 3: two builder lanes that never overlap -- spawned, not concurrent.
    state3 = state_for(plan2, builders2, reviews2, shape="diamond")
    events3 = [
        ev(10.0, "builder", "b-1", "start"),
        ev(11.0, "builder", "b-1", "tool", "Edit"),
        ev(20.0, "builder", "b-2", "start"),
        ev(21.0, "builder", "b-2", "tool", "Edit"),
    ]
    write_run(root, "r3", state3, events3)
    code, out = run(root, "r3")
    check("case3 no overlap", "0/1 pair(s) overlap" in out, True)
    check("case3 not proven concurrent", "not proven concurrent" in out, True)

    # -- case 4: single-loop shape never claims concurrency, even with 2+ builder lanes.
    state4 = state_for(plan, builders, reviews, shape="single-loop")
    write_run(root, "r4", state4, events3)
    code, out = run(root, "r4")
    check("case4 single-loop N/A", "concurrency is not claimed, N/A" in out, True)

    # -- case 5: no activity.jsonl at all -- must not crash, must say so plainly.
    write_run(root, "r5", state_for(plan, builders, reviews), None)
    code, out = run(root, "r5")
    check("case5 exit code", code, 0)
    check("case5 no activity message", "nothing to measure" in out, True)

    # -- case 6: no run id, no .graph/CURRENT -- clean failure, not a traceback.
    proc = subprocess.run([sys.executable, script], cwd=root, capture_output=True, text=True)
    check("case6 exit code", proc.returncode, 1)
    check("case6 stderr names the problem",
          "no run given" in proc.stderr, True)

    # -- case 7: bad run id -- clean failure, not a traceback.
    code, _ = run(root, "does-not-exist")
    check("case7 exit code", code, 1)

    print()
    if FAILURES:
        print("%d FAILURE(S): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
