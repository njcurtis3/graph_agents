#!/usr/bin/env python
"""PostToolUse hook: flag CURRENT-STATE.md stale when the fleet's definition changes.

DELIBERATE, USER-CONFIRMED (2026-08-25): flag only, never auto-stamp. Do not "fix" this.

Deliberately does NOT auto-stamp the date. "Last verified" must mean a human or agent
actually re-checked the snapshot against disk; a bot bumping the date would make the
doc confidently wrong, which is the exact failure CURRENT-STATE.md warns about.
Instead this injects context telling Claude the snapshot is now stale.

Exit 0 always — a hook must never block a legitimate edit.
"""
import json, os, sys

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

    norm = str(path).replace("\\", "/")
    base = os.path.basename(norm)

    # Only the fleet's own definition files.
    if "/graph_agents/" not in norm and not norm.endswith("/graph_agents"):
        return
    if base == "CURRENT-STATE.md":          # never self-trigger
        return
    if "/.graph/runs/" in norm:             # run state churns; not an architecture change
        return
    if not (norm.endswith(".md") or norm.endswith(".json")):
        return

    rel = norm.split("/graph_agents/", 1)[-1]
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"[fleet-state] You just changed `graph_agents/{rel}`, which is part of the "
                "agent architecture's definition. `graph_agents/CURRENT-STATE.md` is now STALE.\n"
                "Before this turn ends: re-verify the affected rows against disk (do not trust "
                "memory), update the relevant section, append a one-line Changelog entry, and set "
                "`Last verified:` to today's date. If nothing material changed for the snapshot, "
                "say so explicitly rather than silently skipping it."
            ),
        }
    }, sys.stdout)

main()
