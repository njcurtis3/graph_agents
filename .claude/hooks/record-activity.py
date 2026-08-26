#!/usr/bin/env python
"""Heartbeat: append one line per node event to the open run's activity log.

The overseer this fleet wanted is not an agent. A subagent is spawned, runs, returns
text and ends -- there is no loop it could watch from, no channel to its siblings, and a
node that consumes nothing and produces nothing is the fake edge `GRAPH.md` says to
delete. The hook layer, by contrast, already runs alongside every node and is handed
`agent_id` and `agent_type` on every tool event, plus `SubagentStart`/`SubagentStop`.

So this writes `.graph/runs/<run>/activity.jsonl`: one compact JSON object per line.

    {"t": 1756209600.4, "ev": "start", "agent": "builder",  "id": "abc123"}
    {"t": 1756209601.9, "ev": "tool",  "agent": "builder",  "id": "abc123", "tool": "Edit"}
    {"t": 1756209640.2, "ev": "stop",  "agent": "builder",  "id": "abc123"}

Which is enough for four things the fleet could not previously answer:

  live status      what is running right now, and what it just did
  model tiering    GRAPH.md argues cost hard and has never measured it: duration and
                   tool counts per agent_type are the evidence
  independence     a re-review's `SubagentStart` carries a NEW agent_id, which is what
                   makes "a fresh reviewer" checkable rather than merely asserted
  real parallelism when a diamond finally runs, overlapping timestamps are what prove
                   the builders actually ran concurrently

`agent_type` is absent for the main session, so those events are recorded as
`orchestrator` -- it is a participant in the run and its writes belong in the record.

Silent when no run is open or the run is closed. Never blocks, never raises: an
unwritable log must not cost a tool call. Exit 0 always.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.realpath(__file__))
FLEET = os.path.normpath(os.path.join(HERE, "..", ".."))
CURRENT = os.path.join(FLEET, ".graph", "CURRENT")
CLOSED = ("done", "blocked")
MAX_LINES = 20000        # a runaway loop must not fill a disk


def open_run_dir():
    try:
        with open(CURRENT, encoding="utf-8") as fh:
            run_id = fh.read().strip()
        if not run_id:
            return None
        run_dir = os.path.join(FLEET, ".graph", "runs", run_id)
        with open(os.path.join(run_dir, "state.json"), encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(state, dict):
        return None
    if str(state.get("status") or "").strip().lower() in CLOSED:
        return None
    return run_dir


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    event = {"SubagentStart": "start", "SubagentStop": "stop",
             "PostToolUse": "tool"}.get(payload.get("hook_event_name"))
    if event is None:
        return

    run_dir = open_run_dir()
    if run_dir is None:
        return

    line = {
        "t": round(time.time(), 1),
        "ev": event,
        "agent": str(payload.get("agent_type") or "orchestrator").strip(),
    }
    if payload.get("agent_id"):
        line["id"] = str(payload["agent_id"])
    if event == "tool" and payload.get("tool_name"):
        line["tool"] = str(payload["tool_name"])

    path = os.path.join(run_dir, "activity.jsonl")
    try:
        # Cheap guard, checked only occasionally: counting every line on every tool
        # call would make the log cost more than the work it records.
        if event == "start" and os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                if sum(1 for _ in fh) >= MAX_LINES:
                    return
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, separators=(",", ":")) + "\n")
    except OSError:
        return


main()
