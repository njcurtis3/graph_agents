"""Tests for flag-stale-state.py: which edits make CURRENT-STATE.md stale, and which
only look like they do.

This hook had no tests until 2026-09-19, which is how gap #15 lived as long as it did --
it fired on every app-file edit made inside a builder's worktree, telling a builder it
had changed the agent architecture when it had changed a fixture. Noise, not damage, but
noise from a hook that exists to be heeded is how the real warning gets ignored later.

The hook is a subprocess rather than an import: its filename is not an identifier, and
running it the way Claude Code runs it also proves it exits 0 and emits parseable JSON.

Run: python test_flag_stale_state.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
HOOK = os.path.join(HERE, "flag-stale-state.py")
FLEET = os.path.normpath(os.path.join(HERE, "..", ".."))
UMBRELLA = os.path.dirname(FLEET)

checks = []


def check(name, cond):
    checks.append((name, bool(cond)))
    print("  %s %s" % ("ok  " if cond else "FAIL", name))


def fire(path, response=None):
    """(fired, message). Runs the hook exactly as the harness does."""
    payload = {"hook_event_name": "PostToolUse", "tool_name": "Edit",
               "tool_input": {"file_path": path}}
    if response is not None:
        payload["tool_response"] = response
    proc = subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                          capture_output=True, text=True)
    assert proc.returncode == 0, "the hook must never block a write: %s" % proc.stderr
    out = proc.stdout.strip()
    if not out:
        return False, ""
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    return True, context


def at(*parts):
    return os.path.join(FLEET, *parts)


print("definition drift fires:")
fired, message = fire(at(".claude", "hooks", "record-activity.py"))
check("a fleet hook .py makes the snapshot stale", fired)
check("...and the message says which file did it",
      "record-activity.py" in message and "STALE" in message)
check("a fleet .md makes the snapshot stale", fire(at("GRAPH.md"))[0])
check("a fleet .json makes the snapshot stale",
      fire(at("portfolio", "registry.json"))[0])
check("CURRENT-STATE.md never triggers itself",
      fire(at("CURRENT-STATE.md"))[0] is False)
check("a non-definition extension in the fleet is silent",
      fire(at("notes.txt"))[0] is False)

print("\nHISTORY.md is the other half of the snapshot, not a definition (2026-09-22):")
# Split out of CURRENT-STATE.md: the closed-run narratives and the Changelog. Firing on it
# would tell whoever just appended the required Changelog row that they now owe one.
check("HISTORY.md never triggers, exactly like CURRENT-STATE.md",
      fire(at("HISTORY.md"))[0] is False)
check("a definition edit names HISTORY.md as where the Changelog row goes",
      "HISTORY.md" in fire(at("GRAPH.md"))[1])
check("...and no longer asks for a Changelog entry in CURRENT-STATE.md",
      "Changelog entry to `graph_agents/HISTORY.md`" in fire(at("GRAPH.md"))[1])

print("\nan app's own files are not the fleet:")
check("an app file outside the fleet is silent",
      fire(os.path.join(UMBRELLA, "huntstack", "apps", "web", "main.tsx"))[0] is False)

print("\nand neither is an app file inside a builder worktree (gap #15):")
# The worktree lives under the fleet ONLY because `repos/` is not a git repo, so there is
# nowhere else inside the umbrella to put one. Everything in it belongs to the app.
worktree = at(".graph", "worktrees", "2026-08-26-archive-adapters")
check("a worktree app source file is silent",
      fire(os.path.join(worktree, "src", "adapters", "__init__.py"))[0] is False)
check("a worktree fixture -- the exact edit that reported this -- is silent",
      fire(os.path.join(worktree, "fixtures", "whoop", "sleep.json"))[0] is False)
check("a worktree markdown file is silent",
      fire(os.path.join(worktree, "README.md"))[0] is False)
check("the same relative path OUTSIDE a worktree still fires",
      fire(at("conventions", "mobile-first.md"))[0])

print("\nhistory drift fires only on a CLOSED run:")
runs = at(".graph", "runs")
done = None
for name in sorted(os.listdir(runs)):
    state = os.path.join(runs, name, "state.json")
    if not os.path.isfile(state):
        continue
    try:
        with open(state, encoding="utf-8") as fh:
            status = str(json.load(fh).get("status", "")).lower()
    except (OSError, ValueError):
        continue
    if status == "done":
        done = state
        break

check("a run that reached done makes the snapshot stale on HISTORY",
      done is not None and fire(done)[0])
check("...and says so in the message",
      done is not None and "HISTORY" in fire(done)[1])
check("...and sends the Runs table row to CURRENT-STATE.md",
      done is not None and "Runs table" in fire(done)[1]
      and "CURRENT-STATE.md" in fire(done)[1])
check("...and the narrative and Changelog row to HISTORY.md",
      done is not None and "graph_agents/HISTORY.md" in fire(done)[1]
      and "what happened" in fire(done)[1])
check("a mid-run state.json write is silent",
      fire(os.path.join(runs, "no-such-run", "state.json"))[0] is False)
check("_schema.json is a DEFINITION file, not run state",
      "STALE on its HISTORY" not in fire(os.path.join(runs, "_schema.json"))[1])

print("\nthe payload shapes the harness actually sends:")
check("a tool_response filePath is read when tool_input has none",
      subprocess.run([sys.executable, HOOK],
                     input=json.dumps({"hook_event_name": "PostToolUse",
                                       "tool_name": "Write",
                                       "tool_input": {},
                                       "tool_response": {"filePath": at("GRAPH.md")}}),
                     capture_output=True, text=True).stdout.strip() != "")
check("a payload with no path at all is silent and exits 0",
      subprocess.run([sys.executable, HOOK], input=json.dumps({"tool_input": {}}),
                     capture_output=True, text=True).stdout.strip() == "")
check("malformed stdin is silent and exits 0",
      subprocess.run([sys.executable, HOOK], input="not json",
                     capture_output=True, text=True).returncode == 0)

passed = sum(1 for _, ok in checks if ok)
print("\n%d/%d checks passed" % (passed, len(checks)))
if passed != len(checks):
    sys.exit(1)
