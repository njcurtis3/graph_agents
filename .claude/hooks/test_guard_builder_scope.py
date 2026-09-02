#!/usr/bin/env python
"""Self-test for guard-builder-scope.py. Stdlib only, no pytest.

    python graph_agents/.claude/hooks/test_guard_builder_scope.py

This guard has silently regressed TWICE, and both times nothing noticed until a run
paid for it:

  * it denied every write by every builder in a diamond, from the day it was written
    until the first run actually fanned out (see the worktree comment in the hook);
  * it denied every write under a `**` directory entry, which cost three slices of
    `2026-09-01-huntstack-mobile` a round trip on 2026-09-01.

Both are matcher bugs, and a matcher is exactly the kind of thing a test pins down
cheaply. The point of this file is that the NEXT one fails here instead of in a run.

It drives the hook as a subprocess through real stdin payloads, the way Claude Code
does, so it tests the actual contract (deny JSON on stdout, silence otherwise) rather
than imported internals.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
HOOK = os.path.join(HERE, "guard-builder-scope.py")
FLEET = os.path.normpath(os.path.join(HERE, "..", ".."))
UMBRELLA = os.path.dirname(FLEET)

FAILURES = []


def run_hook(payload):
    """(denied, reason). Mirrors how Claude Code invokes the hook."""
    proc = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        # Exit 0 always is a documented invariant of the hook.
        FAILURES.append("hook exited %d, stderr: %s" % (proc.returncode, proc.stderr[:400]))
        return None, proc.stderr
    out = proc.stdout.strip()
    if not out:
        return False, ""
    try:
        decision = json.loads(out)["hookSpecificOutput"]
    except Exception:
        FAILURES.append("hook emitted unparseable stdout: %r" % out[:400])
        return None, out
    return decision.get("permissionDecision") == "deny", decision.get("permissionDecisionReason", "")


def check(label, got, want):
    if got == want:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s -- expected %s, got %s" % (label, want, got))
        FAILURES.append(label)


def with_run(state, body):
    """Point .graph/CURRENT at a temporary run, run `body`, always restore."""
    runs = os.path.join(FLEET, ".graph", "runs")
    current = os.path.join(FLEET, ".graph", "CURRENT")
    previous = None
    if os.path.exists(current):
        with open(current, encoding="utf-8") as fh:
            previous = fh.read()
    run_dir = tempfile.mkdtemp(prefix="guardtest-", dir=runs)
    try:
        with open(os.path.join(run_dir, "state.json"), "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        with open(current, "w", encoding="utf-8") as fh:
            fh.write(os.path.basename(run_dir))
        body(run_dir)
    finally:
        if previous is None:
            os.remove(current)
        else:
            with open(current, "w", encoding="utf-8") as fh:
                fh.write(previous)
        for name in os.listdir(run_dir):
            os.remove(os.path.join(run_dir, name))
        os.rmdir(run_dir)


def state_with(files):
    return {
        "run_id": "guard-self-test",
        "status": "building",
        "approved_by_human": True,
        "architect": {"plan": [{"slice": "s1", "files": files}]},
    }


def builder_writing(path):
    return {"agent_type": "builder", "tool_name": "Write",
            "tool_input": {"file_path": os.path.join(UMBRELLA, path)}}


def main():
    print("guard-builder-scope self-test\n")

    # --- The 2026-09-01 regression: a `**` entry must cover the tree beneath it. ---
    print("glob directory entries (`**`):")

    def globbed(_run_dir):
        check("package.json under apps/mobile/** is ALLOWED",
              run_hook(builder_writing("huntstack/apps/mobile/package.json"))[0], False)
        check("a nested route under apps/mobile/** is ALLOWED",
              run_hook(builder_writing("huntstack/apps/mobile/src/app/index.tsx"))[0], False)
        check("the bare directory itself is ALLOWED",
              run_hook(builder_writing("huntstack/apps/mobile"))[0], False)
        # The guard must still guard: widening it to cover everything would be a worse
        # bug than the one being fixed.
        check("a sibling app is DENIED",
              run_hook(builder_writing("huntstack/apps/web/src/main.tsx"))[0], True)
        check("a path that merely shares a prefix is DENIED",
              run_hook(builder_writing("huntstack/apps/mobile-extra/x.ts"))[0], True)
        check("another repo entirely is DENIED",
              run_hook(builder_writing("podcraft-ai/src/x.py"))[0], True)

    with_run(state_with(["huntstack/apps/mobile/**"]), globbed)

    # --- Literal entries must behave exactly as they did before the fix. ---
    print("\nliteral entries (unchanged behaviour):")

    def literal(_run_dir):
        check("the exact approved file is ALLOWED",
              run_hook(builder_writing("huntstack/.github/workflows/ci.yml"))[0], False)
        check("a different file in the same directory is DENIED",
              run_hook(builder_writing("huntstack/.github/workflows/release.yml"))[0], True)

    with_run(state_with(["huntstack/.github/workflows/ci.yml"]), literal)

    # --- A wildcard deeper in the entry falls through to fnmatch. ---
    print("\nresidual wildcards (`a/**/*.ts`):")

    def deep(_run_dir):
        check("a matching extension is ALLOWED",
              run_hook(builder_writing("huntstack/apps/mobile/src/lib/api.ts"))[0], False)
        check("a non-matching extension is DENIED",
              run_hook(builder_writing("huntstack/apps/mobile/src/lib/api.js"))[0], True)

    with_run(state_with(["huntstack/apps/mobile/**/*.ts"]), deep)

    # --- The guard's documented silences. ---
    print("\ndocumented silences:")

    def silences(run_dir):
        check("a non-builder is UNCONSTRAINED",
              run_hook({"agent_type": "orchestrator", "tool_name": "Write",
                        "tool_input": {"file_path": os.path.join(UMBRELLA, "anything/at/all.txt")}})[0],
              False)
        check("the run's own state.json is ALLOWED",
              run_hook({"agent_type": "builder", "tool_name": "Write",
                        "tool_input": {"file_path": os.path.join(run_dir, "state.json")}})[0],
              False)

    with_run(state_with(["huntstack/apps/mobile/**"]), silences)

    def unapproved(_run_dir):
        check("an unapproved run does not deadlock (audit owns that finding)",
              run_hook(builder_writing("huntstack/apps/web/src/main.tsx"))[0], False)

    unapproved_state = state_with(["huntstack/apps/mobile/**"])
    unapproved_state["approved_by_human"] = False
    with_run(unapproved_state, unapproved)

    def closed(_run_dir):
        check("a closed run does not constrain the next builder",
              run_hook(builder_writing("huntstack/apps/web/src/main.tsx"))[0], False)

    closed_state = state_with(["huntstack/apps/mobile/**"])
    closed_state["status"] = "done"
    with_run(closed_state, closed)

    # --- Fail-closed (gap #17, closed 2026-09-02). ---
    # A crashing guard used to be indistinguishable from a guard with no opinion, so a
    # typo in the hook silently stopped guarding builders instead of blocking them.
    # These cases pin the corrected failure direction.
    print("\nfail-closed behaviour:")

    def broken(_run_dir):
        # A real fault injected into a real copy of the hook, run from this directory so
        # its FLEET/UMBRELLA paths still resolve. Asserting against a hand-written stub
        # would only prove the stub works.
        source = open(HOOK, encoding="utf-8").read()
        needle = "    payload = json.load(sys.stdin)\n"
        assert needle in source, "hook shape changed; update this fault injection"
        broken_path = os.path.join(HERE, "_selftest_broken_guard.py")
        with open(broken_path, "w", encoding="utf-8") as fh:
            fh.write(source.replace(
                needle,
                needle + '    raise RuntimeError("injected fault for the self-test")\n',
                1,
            ))
        try:
            proc = subprocess.run(
                [sys.executable, broken_path],
                input=json.dumps(builder_writing("huntstack/apps/mobile/package.json")),
                capture_output=True, text=True,
            )
            out = proc.stdout.strip()
            denied = names_itself = False
            if out:
                decision = json.loads(out)["hookSpecificOutput"]
                denied = decision.get("permissionDecision") == "deny"
                names_itself = "GUARD ITSELF IS BROKEN" in decision.get(
                    "permissionDecisionReason", "")
            check("a crashing guard DENIES rather than silently allowing", denied, True)
            check("the denial names the guard, not the builder", names_itself, True)
            check("a crashing guard still exits 0", proc.returncode, 0)
        finally:
            os.remove(broken_path)

    with_run(state_with(["huntstack/apps/mobile/**"]), broken)

    def malformed(_run_dir):
        # The one remaining allow-on-failure, and it is deliberate: with no parseable
        # payload there is no agent_type, so the deny could not be scoped to builders
        # and would block every agent in the session.
        proc = subprocess.run([sys.executable, HOOK], input="not json at all",
                              capture_output=True, text=True)
        check("a malformed payload is ALLOWED (cannot be scoped to builders)",
              proc.stdout.strip(), "")
        check("a malformed payload still exits 0", proc.returncode, 0)

    with_run(state_with(["huntstack/apps/mobile/**"]), malformed)

    print()
    if FAILURES:
        print("FAILED (%d):" % len(FAILURES))
        for f in FAILURES:
            print("  - %s" % f)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
