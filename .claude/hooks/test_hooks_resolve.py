#!/usr/bin/env python
"""Every hook command in settings.json must actually find and run its script.

    python graph_agents/.claude/hooks/test_hooks_resolve.py

This exists because of gap #18. Every hook command was written cwd-relative
(`python graph_agents/.claude/hooks/X.py`), so from anywhere other than `repos/` the
path resolved to `graph_agents/graph_agents/...` and the script was simply not found.
Six of the seven also carried `2>/dev/null || true`, which discarded the error and
forced the exit code to 0 -- so they reported success while doing nothing at all. How
long they had been silently dead is unknown, because nothing could tell.

The lesson is not "fix the paths". It is that a hook which cannot be observed failing
will eventually fail unobserved. This test is the observation.

It parses the REAL commands out of settings.json rather than hardcoding a list, so a
hook added later is covered without anyone remembering to update this file. It runs
each one from a directory that is NOT the umbrella root, which is the exact condition
that used to break them.
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
FLEET = os.path.normpath(os.path.join(HERE, "..", ".."))
UMBRELLA = os.path.dirname(FLEET)
SETTINGS = os.path.join(FLEET, ".claude", "settings.json")

# A benign payload: a non-builder editing a fleet doc. Every hook should either act on
# it or ignore it, and none should crash.
PAYLOAD = json.dumps({
    "agent_type": "orchestrator",
    "tool_name": "Write",
    "tool_input": {"file_path": os.path.join(FLEET, "README.md")},
    "tool_response": {},
})

# The signature of the bug this test exists for.
NOT_FOUND = re.compile(r"can't open file|No such file or directory|ModuleNotFoundError")

failures = []


def commands():
    """(event, command) for every hook command configured, in file order."""
    with open(SETTINGS, encoding="utf-8") as fh:
        settings = json.load(fh)
    for event, matchers in (settings.get("hooks") or {}).items():
        for matcher in matchers:
            for hook in matcher.get("hooks") or []:
                if hook.get("type") == "command" and hook.get("command"):
                    yield event, hook["command"]


def main():
    print("hook command resolution (run from a NON-root cwd, the condition that broke them)\n")

    # Anywhere but the umbrella root. This is the whole point of the test.
    cwd = FLEET
    assert os.path.normpath(cwd) != os.path.normpath(UMBRELLA)

    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = UMBRELLA

    # Run through a POSIX shell explicitly. `shell=True` on Windows is cmd.exe, which
    # does not expand `${VAR:-default}` and passes it through literally -- that would
    # fail every hook here and report a bug that does not exist. Claude Code runs hook
    # commands through a POSIX shell (verified: an Edit from a non-root cwd succeeds
    # with the `${CLAUDE_PROJECT_DIR:-.}` form, and the scope guard has no `|| true`
    # left to hide a failure), so match that.
    bash = shutil.which("bash")
    if not bash:
        print("  SKIP no POSIX shell found; cannot check the commands as written")
        return 0

    seen = 0
    for event, command in commands():
        seen += 1
        script = command.split("/")[-1].split('"')[0] or command
        proc = subprocess.run([bash, "-c", command], cwd=cwd, env=env,
                              input=PAYLOAD, capture_output=True, text=True)
        blob = (proc.stderr or "") + (proc.stdout or "")
        if NOT_FOUND.search(blob):
            print("  FAIL %-28s %s -- %s" % (script, event, blob.strip().splitlines()[0][:90]))
            failures.append(script)
        else:
            print("  ok   %-28s %s" % (script, event))

    if not seen:
        print("  FAIL no hook commands found in settings.json -- did its shape change?")
        failures.append("settings.json")

    print("\n%d hook command(s) checked" % seen)
    if failures:
        print("FAILED: %s" % ", ".join(failures))
        print("A hook whose script cannot be found reports success and does nothing.")
        return 1
    print("all hook commands resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
