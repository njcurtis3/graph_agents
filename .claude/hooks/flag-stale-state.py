#!/usr/bin/env python
"""PostToolUse hook: flag CURRENT-STATE.md stale when the fleet's definition changes.

DELIBERATE, USER-CONFIRMED (2026-08-25): flag only, never auto-stamp. Do not "fix" this.

Deliberately does NOT auto-stamp the date. "Last verified" must mean a human or agent
actually re-checked the snapshot against disk; a bot bumping the date would make the
doc confidently wrong, which is the exact failure CURRENT-STATE.md warns about.
Instead this injects context telling Claude the snapshot is now stale.

Two kinds of drift are flagged, because the snapshot can go false either way:

  DEFINITION drift  a fleet .md/.json changed -- the graph is described wrongly now.
  HISTORY drift     a run reached status "done" -- the graph DID something the
                    snapshot's Status line, Runs table and Changelog do not know about.
                    Mid-run writes stay silent: run state churns, and only a closed run
                    changes what is true about the fleet.

`repos/.claude` is a directory junction into `graph_agents/.claude`, so every fleet
definition file has two valid absolute paths and only one of them contains the
"/graph_agents/" segment -- and GRAPH.md tells agents to use the OTHER one. Resolve the
path before routing on it or the hook is silent on exactly the documented path.

Exit 0 always -- a hook must never block a legitimate edit.
"""
import json, os, sys


def _resolve(path):
    """Absolute, forward-slashed, junction/symlink-resolved. Never raises."""
    try:
        real = os.path.realpath(path)
    except Exception:
        real = path
    if not os.path.isabs(str(real)):
        try:
            real = os.path.abspath(real)
        except Exception:
            pass
    return str(real).replace("\\", "/")


def _run_is_done(path):
    """True only for a .graph/runs/<id>/state.json whose status is 'done'."""
    try:
        with open(path, encoding="utf-8") as fh:
            return str(json.load(fh).get("status", "")).strip().lower() == "done"
    except Exception:
        return False


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    ti = payload.get("tool_input") or {}
    tr = payload.get("tool_response") or {}
    path = ti.get("file_path") or (tr.get("filePath") if isinstance(tr, dict) else None)
    if not path:
        return

    norm = _resolve(path)
    base = os.path.basename(norm)

    # Only the fleet's own files.
    if "/graph_agents/" not in norm and not norm.endswith("/graph_agents"):
        return
    if base == "CURRENT-STATE.md":          # never self-trigger
        return

    rel = norm.split("/graph_agents/", 1)[-1]

    # -- history drift: a run closed. Only on close, never on every mid-run write.
    # `_schema.json` also lives here but is a DEFINITION file, not run state: it falls
    # through to the definition branch below.
    if "/.graph/runs/" in norm and base != "_schema.json":
        if base != "state.json" or not _run_is_done(norm):
            return
        message = (
            f"[fleet-state] Run `{rel}` is now `status: done`. A closed run is a fact "
            "about what this fleet has actually executed, so "
            "`graph_agents/CURRENT-STATE.md` is now STALE on its HISTORY.\n"
            "Before this turn ends: add the run to the Runs table with its app, shape and "
            "outcome, give it its own `### <run-id> — what happened` heading (insert it "
            "ABOVE the narrative it describes, never above another run's prose), re-check "
            "the Status line and the 'has executed?' column of the node roster against "
            "this run, append a one-line Changelog entry, and set `Last verified:` to "
            "today's date."
        )
    else:
        # -- definition drift. `.py` counts: verify-state.py and this hook are tracked
        # in the snapshot's "What is live" table down to their line counts.
        if not norm.endswith((".md", ".json", ".py")):
            return
        message = (
            f"[fleet-state] You just changed `graph_agents/{rel}`, which is part of the "
            "agent architecture's definition. `graph_agents/CURRENT-STATE.md` is now STALE.\n"
            "Before this turn ends: re-verify the affected rows against disk (do not trust "
            "memory), update the relevant section, append a one-line Changelog entry, and set "
            "`Last verified:` to today's date. If nothing material changed for the snapshot, "
            "say so explicitly rather than silently skipping it."
        )

    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": message,
        }
    }, sys.stdout)


main()
