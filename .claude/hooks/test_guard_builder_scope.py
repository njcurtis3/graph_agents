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

Since 2026-09-06 the guard also runs on `Bash` (gap #13), which is a THIRD outcome to
pin: a command whose write target cannot be resolved is allowed WITH A WARNING, and a
warning that quietly became a denial would deny a fifteenth of every builder's commands.
So the Bash section below asserts allow / warn / deny separately rather than asserting
"not denied".

It drives the hook as a subprocess through real stdin payloads, the way Claude Code
does, so it tests the actual contract (deny JSON on stdout, silence otherwise) rather
than imported internals.
"""
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.realpath(__file__))
HOOK = os.path.join(HERE, "guard-builder-scope.py")
FLEET = os.path.normpath(os.path.join(HERE, "..", ".."))
UMBRELLA = os.path.dirname(FLEET)

# The one thing imported rather than driven through stdin. The cap cases below have to
# sit either side of the classifier's real limit, and a second copy of the number here
# would drift from the one the hook enforces -- which is the bug those cases exist for.
sys.path.insert(0, HERE)
from bash_write_targets import MAX_COMMAND        # noqa: E402

FAILURES = []


def hook_decision(payload, run_in=None):
    """`hookSpecificOutput` as the hook emitted it; `{}` for silence, None on a fault.

    Every other view in this file is built on this one, so the three outcomes are read
    off the same bytes: a denial carries `permissionDecision`, a warning carries
    `additionalContext` and NO decision at all, and an allow is an empty stdout.

    `run_in` is the hook PROCESS's own cwd, which is not the same thing as the payload's
    and must never be what a relative write target is resolved against -- the hook runs
    wherever the harness happens to launch it.
    """
    proc = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=run_in,
    )
    if proc.returncode != 0:
        # Exit 0 always is a documented invariant of the hook.
        FAILURES.append("hook exited %d, stderr: %s" % (proc.returncode, proc.stderr[:400]))
        return None
    out = proc.stdout.strip()
    if not out:
        return {}
    try:
        return json.loads(out)["hookSpecificOutput"]
    except Exception:
        FAILURES.append("hook emitted unparseable stdout: %r" % out[:400])
        return None


def run_hook(payload):
    """(denied, reason). Mirrors how Claude Code invokes the hook."""
    decision = hook_decision(payload)
    if decision is None:
        return None, ""
    return (decision.get("permissionDecision") == "deny",
            decision.get("permissionDecisionReason", ""))


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


def builder_writing(path, tool="Write"):
    return {"agent_type": "builder", "tool_name": tool,
            "tool_input": {"file_path": os.path.join(UMBRELLA, path)}}


ABSENT = object()      # for a payload that carries no `cwd` at all


def builder_running(command, agent="builder", cwd=None):
    """A `Bash` PreToolUse payload, shaped the way the harness sends one.

    `cwd` is what a relative target resolves against. It defaults to the umbrella
    because that is the launch rule and it is where the Bash tool actually runs.
    """
    payload = {"agent_type": agent, "tool_name": "Bash",
               "tool_input": {"command": command}}
    if cwd is not ABSENT:
        payload["cwd"] = UMBRELLA if cwd is None else cwd
    return payload


def outcome(command, agent="builder", cwd=None, run_in=None):
    """("allow" | "warn" | "deny", the text that came with it).

    Three outcomes, not two. `warn` is the unresolved-write-shape branch, and calling it
    "not denied" would let it become a denial without this file noticing.
    """
    decision = hook_decision(builder_running(command, agent=agent, cwd=cwd),
                             run_in=run_in)
    if decision is None:
        return "hook-fault", ""
    if decision.get("permissionDecision") == "deny":
        return "deny", decision.get("permissionDecisionReason", "")
    if decision.get("additionalContext"):
        return "warn", decision["additionalContext"]
    return "allow", ""


def heredoc(target, body="hello"):
    return "cat <<'EOF' > %s\n%s\nEOF" % (target, body)


def heredoc_of(target, size):
    """A heredoc writing `target` whose whole command string is at least `size` chars."""
    return heredoc(target, "x" * size)


def with_faulted_hook(needle, replacement, body):
    """Write a copy of the hook with ONE substitution applied, hand `body` its path.

    A real fault in a real copy, living in this directory so the copy's FLEET and
    UMBRELLA still resolve to the same places. Asserting against a hand-written stub
    would only prove the stub works, and the failure directions below are the whole
    reason this guard is allowed to be strict.
    """
    source = open(HOOK, encoding="utf-8").read()
    assert needle in source, "hook shape changed; update this fault injection: %r" % needle
    faulted = os.path.join(HERE, "_selftest_broken_guard.py")
    with open(faulted, "w", encoding="utf-8") as fh:
        fh.write(source.replace(needle, replacement, 1))
    try:
        body(faulted)
    finally:
        os.remove(faulted)


def ask(hook_path, payload):
    """(exit code, decision dict) from an arbitrary copy of the hook."""
    proc = subprocess.run([sys.executable, hook_path], input=json.dumps(payload),
                          capture_output=True, text=True)
    out = proc.stdout.strip()
    if not out:
        return proc.returncode, {}
    try:
        return proc.returncode, json.loads(out)["hookSpecificOutput"]
    except Exception:
        FAILURES.append("faulted hook emitted unparseable stdout: %r" % out[:400])
        return proc.returncode, {}


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

    # --- Bash writes (gap #13, closed for what the classifier can resolve). ---
    # Registered on `Write|Edit` alone, this guard watched two of the three ways a
    # builder writes a file. `sed -i`, a heredoc, `tee` and a plain redirect went
    # through the approved set without a denial, a record or a trace.
    print("\nbash writes -- resolved targets are judged like a Write:")

    def bash(run_dir):
        check("an out-of-scope heredoc is DENIED",
              outcome(heredoc("huntstack/apps/web/main.tsx"))[0], "deny")
        check("an in-scope heredoc is ALLOWED",
              outcome(heredoc("huntstack/apps/mobile/App.tsx"))[0], "allow")
        check("an out-of-scope `sed -i` is DENIED",
              outcome("sed -i 's/a/b/' huntstack/apps/web/main.tsx")[0], "deny")
        check("an in-scope `sed -i` is ALLOWED",
              outcome("sed -i 's/a/b/' huntstack/apps/mobile/App.tsx")[0], "allow")
        # A delete outside the set is a modification of the tree the plan is about.
        check("an out-of-scope `rm -rf` is DENIED",
              outcome("rm -rf huntstack/apps/web")[0], "deny")
        check("an out-of-scope `tee` is DENIED",
              outcome("echo x | tee huntstack/apps/web/main.tsx")[0], "deny")
        check("an out-of-scope `python -c` write is DENIED",
              outcome("python -c \"open('huntstack/apps/web/m.tsx','w').write('x')\"")[0],
              "deny")

        # A `cd` moves what a relative target means, and the classifier applies it. If
        # the guard judged the bare target instead it would deny approved work.
        check("a `cd` into the approved directory is ALLOWED",
              outcome("cd huntstack/apps/mobile && echo x > App.tsx")[0], "allow")
        check("a `cd` that lands outside it is DENIED",
              outcome("cd huntstack/apps && echo x > web/main.tsx")[0], "deny")

        # ...and a relative target with no `cd` is relative to the SHELL's cwd, which
        # the payload carries. Judging it against anything else is not a near miss: the
        # same three words name a different file, so the guard would deny approved work
        # and allow unapproved work with equal confidence.
        check("a relative target is resolved against the payload's cwd",
              outcome("echo x > App.tsx",
                      cwd=os.path.join(UMBRELLA, "huntstack", "apps", "mobile"))[0],
              "allow")
        check("...and the same spelling under another cwd is DENIED",
              outcome("echo x > main.tsx",
                      cwd=os.path.join(UMBRELLA, "huntstack", "apps", "web"))[0],
              "deny")
        # No `cwd` in the payload falls back to the launch rule, NOT to wherever the
        # harness happened to start the hook process -- so this one runs the hook from
        # the hooks directory and expects the umbrella's answer anyway.
        check("with no cwd in the payload the launch rule applies, not the hook's own cwd",
              outcome("echo x > huntstack/apps/mobile/App.tsx",
                      cwd=ABSENT, run_in=HERE)[0],
              "allow")

        # The denial has to be actionable: the builder cannot see what the parser saw.
        denied, reason = outcome("sed -i 's/a/b/' huntstack/apps/web/main.tsx")
        check("the denial names the resolved target",
              "huntstack/apps/web/main.tsx" in reason.replace("\\", "/").lower(), True)
        check("the denial quotes the command back", "sed -i" in reason, True)
        check("the denial names the approved set", "huntstack/apps/mobile" in reason, True)

        # ...and it has to READ. Both branches shared one template ending in "... is not
        # in the file set a human approved", which suited a `Write`'s single path and
        # left the Bash branch dangling that predicate after the echoed command, so the
        # builder read it as though the COMMAND were the thing not in the file set. A
        # denial a builder cannot parse is one that gets routed around, so the wording is
        # asserted here and not left to whoever reads the diff.
        check("the Bash denial states the whole claim as one sentence",
              "This Bash command writes a path that is not in the file set a human "
              "approved for run" in reason, True)
        # Ordering, not just presence: the old template put the claim AFTER the echoed
        # command, which is exactly what made it read as though the command were the
        # thing not in the file set. Substring checks cannot see that; position can.
        claim, echoed = reason.find("is not in the file set"), reason.find("sed -i")
        check("...and states that claim BEFORE the command it echoes, never after it",
              claim >= 0 and echoed > claim, True)
        check("...and says how to proceed", "scope_exceptions" in reason, True)
        check("...and agrees in number when several paths are outside",
              "writes paths that are not in the file set"
              in outcome("echo a > huntstack/apps/web/a.tsx && "
                         "echo b > huntstack/apps/web/b.tsx")[1], True)
        # The `Write` branch keeps the wording it already read well with.
        check("the Write denial still names the path and the claim together",
              "main.tsx` is not in the file set a human approved for run"
              in run_hook(builder_writing("huntstack/apps/web/main.tsx"))[1], True)

        print("\n  ...and commands that write nothing pay nothing:")
        for read_only in ("git status", "git diff --stat", "python -m pytest",
                          "node test.js", "grep -rn scope .", "ls -la", "npm run build"):
            check("`%s` is ALLOWED" % read_only, outcome(read_only)[0], "allow")
        check("a redirect to /dev/null is ALLOWED",
              outcome("python -m pytest > /dev/null 2>&1")[0], "allow")
        check("a redirect to a temp file is ALLOWED",
              outcome("echo x > %s" % (tempfile.gettempdir().replace("\\", "/")
                                       + "/guard-selftest-scratch.txt"))[0], "allow")
        check("the run's own state.json is ALLOWED through Bash too",
              outcome("echo x > %s" % os.path.join(run_dir, "state.json").replace("\\", "/"))[0],
              "allow")

        # The fail-OPEN half. This is the branch that closes the "no record" half of
        # gap #13 without closing the "no denial" half, and it must stay an ALLOW: a
        # guard that denies what it merely failed to parse gets routed around.
        print("\n  ...and an unresolvable write shape warns without blocking:")
        state, warned = outcome('echo x > "$OUT"')
        check("an unassigned variable target WARNS, not denies", state, "warn")
        check("the warning says it was allowed", "Allowed" in warned, True)
        check("the warning quotes the command", 'echo x > "$OUT"' in warned, True)
        check("a `$(...)` target WARNS",
              outcome('echo x > "$(mktemp)"')[0], "warn")
        check("a resolved in-scope write alongside an unresolved one WARNS",
              outcome('echo a > huntstack/apps/mobile/App.tsx && echo b > "$OUT"')[0],
              "warn")
        # A denial still wins over a warning: one unreadable target does not buy cover
        # for a readable one that is out of scope.
        check("a resolved OUT-of-scope write alongside an unresolved one DENIES",
              outcome('echo a > huntstack/apps/web/main.tsx && echo b > "$OUT"')[0],
              "deny")

        # No regression on the tools the guard already watched.
        print("\n  ...and Write/Edit are unchanged:")
        check("an out-of-scope Write is still DENIED",
              run_hook(builder_writing("huntstack/apps/web/main.tsx"))[0], True)
        check("an out-of-scope Edit is still DENIED",
              run_hook(builder_writing("huntstack/apps/web/main.tsx", tool="Edit"))[0], True)
        check("an in-scope Edit is still ALLOWED",
              run_hook(builder_writing("huntstack/apps/mobile/App.tsx", tool="Edit"))[0], False)

        # The silences, restated for Bash: each one is a separate early return in the
        # hook and none of them is reached through the Write path.
        print("\n  ...and the silences hold for Bash:")
        check("a non-builder writing out of scope is UNCONSTRAINED",
              outcome("rm -rf huntstack/apps/web", agent="orchestrator")[0], "allow")
        check("a Bash payload with no command is ALLOWED",
              run_hook({"agent_type": "builder", "tool_name": "Bash",
                        "tool_input": {}})[0], False)
        check("a Bash payload whose command is not a string is ALLOWED",
              run_hook({"agent_type": "builder", "tool_name": "Bash",
                        "tool_input": {"command": {"not": "a string"}}})[0], False)

    with_run(state_with(["huntstack/apps/mobile/**"]), bash)

    # --- The escape hatch, which has to reach BOTH tools or it is not an escape. ---
    # `scope_exceptions` is how the orchestrator widens a file set deliberately and
    # auditably. It is read by `approved_paths`, so the Bash branch inherits it for free
    # -- but "for free" is what nobody notices breaking.
    print("\nthe `scope_exceptions` escape hatch reaches Bash too:")

    def excepted(_run_dir):
        check("a Bash write to an excepted path is ALLOWED",
              outcome(heredoc("huntstack/apps/web/main.tsx"))[0], "allow")
        check("a Write to the same excepted path is ALLOWED",
              run_hook(builder_writing("huntstack/apps/web/main.tsx"))[0], False)
        check("...and a path the exception does NOT name is still DENIED",
              outcome(heredoc("huntstack/apps/web/other.tsx"))[0], "deny")

    granted = state_with(["huntstack/apps/mobile/**"])
    granted["scope_exceptions"] = ["huntstack/apps/web/main.tsx"]
    with_run(granted, excepted)

    # --- The classifier's length cap, and the hook's ordering around it. ---
    # `classify` checks `MAX_COMMAND` BEFORE its own pre-filter and says why in words:
    # `has_write_signature` is linear in any real command but quadratic in a run of
    # separator characters, so "a cap checked afterwards bounds nothing at all". The hook
    # ran that regex first and checked nothing, which put a 24.3s pre-filter in front of a
    # hook registered with `timeout: 10` -- reached by the one input the cap exists to
    # stop. The stopwatch below is the assertion that would have caught it.
    print("\nthe classifier's length cap runs before the pre-filter:")

    def oversize(_run_dir):
        # A run of separator characters: cheap to type, quadratic to pre-filter, and it
        # writes nothing at all. 601000 characters.
        pathological = ("(" + "a/" * 300) * 1000
        started = time.perf_counter()
        state, text = outcome(pathological)
        elapsed = time.perf_counter() - started
        check("a 601KB pathological command answers in bounded time (%.2fs)" % elapsed,
              elapsed < 5.0, True)
        check("...and answers with a WARNING, not a denial and not silence", state, "warn")
        check("...and the record says the command was too long to parse",
              "longer than the write classifier's cap" in text, True)
        check("...and it does not paste 601KB back into the builder's context",
              len(text) < 5000, True)

        # Finding :416. An over-cap write to an APPROVED path used to be told its target
        # could not be resolved from the command string. It was resolved perfectly -- the
        # classifier hit its cap and never looked. Saying the wrong one of those tells a
        # builder to spell a path literally that already is literal.
        state, text = outcome(heredoc_of("huntstack/apps/mobile/App.tsx",
                                         MAX_COMMAND + 1000))
        check("a large in-scope write WARNS (the cap fired, so nothing was judged)",
              state, "warn")
        check("...and the reason given is the cap, not an unresolvable target",
              ("longer than the write classifier's cap" in text
               and "could not be resolved from the command string" not in text), True)
        check("...and it names the run and the approved set anyway",
              "huntstack/apps/mobile" in text, True)
        # ...and the cap is what changed the answer, not size in general.
        check("the same write just under the cap is still ALLOWED",
              outcome(heredoc_of("huntstack/apps/mobile/App.tsx",
                                 MAX_COMMAND // 2))[0], "allow")
        # The honest hole, pinned so it stays deliberate: past the cap the guard has no
        # opinion about scope, so an OUT-of-scope write is recorded rather than denied.
        check("an over-cap write to an out-of-scope path is recorded, not denied",
              outcome(heredoc_of("huntstack/apps/web/main.tsx",
                                 MAX_COMMAND + 1000))[0], "warn")

    with_run(state_with(["huntstack/apps/mobile/**"]), oversize)

    def bash_closed(_run_dir):
        check("a closed run does not constrain a Bash write",
              outcome("rm -rf huntstack/apps/web")[0], "allow")
        check("a closed run does not even warn on an unresolved shape",
              outcome('echo x > "$OUT"')[0], "allow")

    closed_for_bash = state_with(["huntstack/apps/mobile/**"])
    closed_for_bash["status"] = "done"
    with_run(closed_for_bash, bash_closed)

    def bash_unapproved(_run_dir):
        check("an unapproved run does not deadlock a Bash write",
              outcome("rm -rf huntstack/apps/web")[0], "allow")

    unapproved_for_bash = state_with(["huntstack/apps/mobile/**"])
    unapproved_for_bash["approved_by_human"] = False
    with_run(unapproved_for_bash, bash_unapproved)

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
        needle = "    payload = json.load(sys.stdin)\n"

        def body(faulted):
            code, decision = ask(faulted,
                                 builder_writing("huntstack/apps/mobile/package.json"))
            check("a crashing guard DENIES rather than silently allowing",
                  decision.get("permissionDecision"), "deny")
            check("the denial names the guard, not the builder",
                  "GUARD ITSELF IS BROKEN" in decision.get("permissionDecisionReason", ""),
                  True)
            check("a crashing guard still exits 0", code, 0)

        with_faulted_hook(
            needle,
            needle + '    raise RuntimeError("injected fault for the self-test")\n',
            body)

    with_run(state_with(["huntstack/apps/mobile/**"]), broken)

    def classifier_missing(_run_dir):
        # The gap #17 trap the Bash branch had to step around. The classifier is
        # imported INSIDE `decide()`; imported at module top instead, an ImportError
        # would raise before the fail-closed handler exists, the hook would exit
        # non-zero, and the harness would read that as a hook error and let the write
        # through -- closing gap #13 by silently re-opening #17. Pinned here because
        # moving that import back up is a one-line edit that no other check would see.
        def body(faulted):
            code, decision = ask(faulted,
                                 builder_running("echo x > huntstack/apps/mobile/App.tsx"))
            check("a missing classifier DENIES rather than erroring out of the way",
                  decision.get("permissionDecision"), "deny")
            check("the denial names the guard, not the builder",
                  "GUARD ITSELF IS BROKEN" in decision.get("permissionDecisionReason", ""),
                  True)
            check("a guard with no classifier still exits 0", code, 0)

        with_faulted_hook(
            "from bash_write_targets import MAX_COMMAND, classify, has_write_signature",
            "from bash_write_targets_deliberately_absent import "
            "MAX_COMMAND, classify, has_write_signature",
            body)

    with_run(state_with(["huntstack/apps/mobile/**"]), classifier_missing)

    # --- The pre-filter runs BEFORE any disk I/O. ---
    # This guard now sees every Bash call in the session and re-reads `.graph/CURRENT`
    # and a `state.json` with no caching, so `git status` must return before it touches
    # either. Asserting that from the outside needs a fault, not a stopwatch: make
    # `open_run` itself explode, and a command that never reaches it stays silent while
    # one that does is denied by the fail-closed handler.
    print("\nthe write-signature pre-filter runs before any disk read:")

    def ordering(_run_dir):
        def body(faulted):
            code, decision = ask(faulted, builder_running("git status"))
            check("`git status` never reaches the run state", decision, {})
            check("...and still exits 0", code, 0)
            code, decision = ask(faulted,
                                 builder_running("echo x > huntstack/apps/web/main.tsx"))
            check("a write-shaped command DOES reach it (so the above is not vacuous)",
                  "GUARD ITSELF IS BROKEN" in decision.get("permissionDecisionReason", ""),
                  True)

        with_faulted_hook(
            "def open_run():\n",
            'def open_run():\n    raise RuntimeError("injected: open_run was reached")\n',
            body)

    with_run(state_with(["huntstack/apps/mobile/**"]), ordering)

    print("\nthe one remaining allow-on-failure:")

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
