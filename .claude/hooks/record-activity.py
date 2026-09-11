#!/usr/bin/env python
"""Heartbeat: append one line per node event to the open run's activity log.

The overseer this fleet wanted is not an agent. A subagent is spawned, runs, returns
text and ends -- there is no loop it could watch from, no channel to its siblings, and a
node that consumes nothing and produces nothing is the fake edge `GRAPH.md` says to
delete. The hook layer, by contrast, already runs alongside every node and is handed
`agent_id` and `agent_type` on every tool event, plus `SubagentStart`/`SubagentStop`.

So this writes `.graph/runs/<run>/activity.jsonl`: one compact JSON object per line.

    {"t": 1756209600.4, "ev": "start", "agent": "builder",  "id": "abc123"}
    {"t": 1756209601.9, "ev": "tool",  "agent": "builder",  "id": "abc123", "tool": "Edit", "tokens": 4213}
    {"t": 1756209640.2, "ev": "stop",  "agent": "builder",  "id": "abc123", "tokens": 5890}

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

`parent` (`parent_tool_use_id`, when the payload carries one) is recorded too, added
2026-09-09 to diagnose gap #20: 1,411 of 1,496 `stop` events carry an `agent_id` that
never had a matching `start`, are stamped `orchestrator` for lack of `agent_type`, and
interleave with live work rather than clustering at a run's end -- not what "a subagent
finished" should look like. The leading hypothesis is that the harness fires
`SubagentStop` for something that isn't a `Task`-tool spawn -- a backgrounded `Bash`
process, or an internal tool-use agent behind `WebSearch`/`WebFetch` -- and `parent`
is the field that would show a phantom nested under a real node's own `tool_use_id`
rather than orphaned. Unverified; this only logs the field, it draws no conclusion.

`tokens` (added 2026-09-11) is a real, per-agent-id token total -- NOT derived from the
hook payload, which carries no usage field at all (checked against the hooks reference).
Every subagent writes its own transcript to a location Claude Code owns, not this fleet:
`~/.claude/projects/<encoded cwd>/<session_id>/subagents/agent-<agent_id>.jsonl`, one line
per turn, each carrying a real `message.usage` block (`input_tokens`, `output_tokens`,
`cache_creation_input_tokens`, `cache_read_input_tokens`). On every `tool` and `stop` event
that carries an `agent_id`, this sums those four fields across every line of that specific
agent's transcript and writes the running total as `tokens` -- a cumulative count for that
one instance, so the last value written is that instance's true final count.

This is a real coupling to an undocumented, internal Claude Code storage layout rather
than to any documented hook field -- accepted deliberately (see fleetview's token-counter
work) because the alternative is fabricating a number, and unwritten if the layout doesn't
match: `tokens_used_by` returns `None` on any read/parse failure and the field is simply
omitted from the line, exactly like every other best-effort field here.

Silent when no run is open or the run is closed. Never blocks, never raises: an
unwritable log must not cost a tool call. Exit 0 always.
"""
import json
import os
import re
import sys
import time

TOKEN_FIELDS = ("input_tokens", "output_tokens",
                 "cache_creation_input_tokens", "cache_read_input_tokens")


def encode_cwd(cwd):
    """Mirror Claude Code's own project-directory name for a launch cwd.

    Observed, not documented: `C:\\Users\\natha\\Desktop\\repos` names its project
    directory `C--Users-natha-Desktop-repos` -- every `\\`, `/` and `:` becomes `-`,
    everything else is left alone.
    """
    return re.sub(r"[\\/:]", "-", cwd)


def subagent_transcript_path(payload):
    """Where Claude Code writes ONE subagent's own transcript, or None.

    Needs `cwd`, `session_id` and `agent_id` -- all common hook fields -- present
    together. Absence of any one means this can't be located; that is not this
    fleet's business to fix, just to skip.
    """
    cwd = payload.get("cwd")
    session_id = payload.get("session_id")
    agent_id = payload.get("agent_id")
    if not (cwd and session_id and agent_id):
        return None
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "projects", encode_cwd(str(cwd)),
                         str(session_id), "subagents", "agent-" + str(agent_id) + ".jsonl")


def tokens_used_by(path):
    """Sum of every token field across every turn in one subagent's transcript.

    A running total, not a delta -- callers write it as-is and the last line
    written for a given agent_id is that agent's true final count. Returns None
    (never 0) when the file can't be read at all, so a missing transcript stays
    silent instead of rendering a fabricated zero.
    """
    try:
        fh = open(path, encoding="utf-8")
    except OSError:
        return None
    total = 0
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue        # a torn final line while Claude Code is mid-append
            usage = ((obj.get("message") or {}).get("usage")
                     if isinstance(obj, dict) else None)
            if not isinstance(usage, dict):
                continue
            for field in TOKEN_FIELDS:
                value = usage.get(field)
                if isinstance(value, (int, float)):
                    total += value
    return total

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
    if payload.get("parent_tool_use_id"):
        line["parent"] = str(payload["parent_tool_use_id"])
    if event == "tool" and payload.get("tool_name"):
        line["tool"] = str(payload["tool_name"])
    if event in ("tool", "stop") and payload.get("agent_id"):
        tpath = subagent_transcript_path(payload)
        tokens = tokens_used_by(tpath) if tpath else None
        if tokens is not None:
            line["tokens"] = tokens

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
