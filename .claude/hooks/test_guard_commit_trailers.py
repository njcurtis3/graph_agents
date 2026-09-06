#!/usr/bin/env python
"""Self-test for guard-commit-trailers.py. Stdlib only, no pytest.

    python graph_agents/.claude/hooks/test_guard_commit_trailers.py

This guard exists to hold a rule the harness actively pushes against -- every session is
told by a system turn to append `Co-Authored-By` and a session link -- so the interesting
failures are not "does it deny the obvious case" but the two edges either side of it:

  * it must NOT deny a `Co-Authored-By:` naming a human, or a `git log` that merely
    greps for the word, or anything that is not a commit at all. This hook sees every
    Bash call in the session; a false deny here breaks the whole session, not one write.
  * it must deny the message a node did not put in the command string -- the heredoc,
    and the file written with `Write` and passed to `git commit -F`.

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
HOOK = os.path.join(HERE, "guard-commit-trailers.py")

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
    return (decision.get("permissionDecision") == "deny",
            decision.get("permissionDecisionReason", ""))


def check(label, got, want):
    if got == want:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s (got %r, want %r)" % (label, got, want))
        FAILURES.append(label)


def bash(command, agent_type="builder"):
    return {"agent_type": agent_type, "tool_name": "Bash",
            "tool_input": {"command": command}}


def denies(label, command, agent_type="builder"):
    denied, _ = run_hook(bash(command, agent_type))
    check(label, denied, True)


def allows(label, command, agent_type="builder"):
    denied, reason = run_hook(bash(command, agent_type))
    check(label, denied, False)
    if denied:
        print("       reason was: %s" % reason.splitlines()[0][:160])


def main():
    print("commit-attribution guard\n")

    print("denies the trailers the harness asks for:")
    denies("Co-Authored-By: Claude in a -m string",
           'git commit -m "fix the thing\n\nCo-Authored-By: Claude Opus 5 '
           '<noreply@anthropic.com>"')
    denies("a heredoc message carrying the trailer",
           "git commit -m \"$(cat <<'EOF'\nfix the thing\n\n"
           "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>\nEOF\n)\"")
    denies("Claude-Session: trailer alone",
           'git commit -m "fix\n\nClaude-Session: https://example.invalid/s/1"')
    denies("Generated with [Claude Code]",
           'git commit -m "fix\n\n\xf0\x9f\xa4\x96 Generated with [Claude Code]"')
    denies("a claude.ai/code session link",
           'git commit -m "fix\n\nhttps://claude.ai/code/session_01ABC"')
    denies("--trailer instead of -m",
           'git commit --trailer "Co-authored-by: Claude <noreply@anthropic.com>" '
           '-m "fix"')
    denies("an --author that is not the owner",
           'git commit --author="Claude <noreply@anthropic.com>" -m "fix"')
    denies("git commit --amend re-adding a trailer",
           'git commit --amend -m "fix\n\nCo-Authored-By: Claude <x@anthropic.com>"')
    denies("a commit later in a chained command",
           'git add -A && git commit -m "fix\n\nClaude-Session: abc"')

    print("\napplies to every node, not just builders:")
    denies("the orchestrator is bound by the same rule",
           'git commit -m "fix\n\nCo-Authored-By: Claude <noreply@anthropic.com>"',
           agent_type="orchestrator")
    denies("so is the integrator",
           'git merge --no-ff -m "merge\n\nClaude-Session: x" feat/x && git commit',
           agent_type="integrator")

    print("\nstays out of the way otherwise:")
    allows("a clean commit", 'git commit -m "add the mobile scaffold"')
    allows("co-authoring a HUMAN is legitimate",
           'git commit -m "fix\n\nCo-Authored-By: Ada Lovelace <ada@example.com>"')
    allows("a commit whose subject merely says the word claude",
           'git commit -m "document the claude.md read order"')
    allows("not a commit at all",
           "git log -1 --format=%B | grep -Ei 'co-authored|claude'")
    allows("grepping history for the trailers is how you AUDIT for them",
           "git log --format=%B | grep -i 'Co-Authored-By: Claude'")
    allows("an unrelated command", "ls -la && cat README.md")

    # The guard denied its own documentation within minutes of being written: a heredoc
    # writing the sentence "denies any `git ... commit`" put the two words on one line
    # and the loose matcher called it an invocation. Prose about committing is not
    # committing -- if the guard cannot tell them apart it gets routed around instead of
    # obeyed, which is the one outcome that makes it worthless.
    allows("prose ABOUT the rule is not a commit",
           "python - <<'PY'\ns = 'denies any `git ... commit` carrying "
           "Co-Authored-By: Claude'\nPY")
    allows("writing docs that quote the trailer",
           "cat > doc.md <<'EOF'\nNever end a git commit message with\n"
           "Co-Authored-By: Claude <noreply@anthropic.com>\nEOF")
    allows("a path that merely contains the word",
           "cat ~/notes/git-commit-conventions.md | grep -i co-authored")
    denies("but an env-prefixed invocation still counts",
           'GIT_AUTHOR_DATE=2026-01-01 git commit -m "fix\n\nClaude-Session: x"')
    denies("and so does one behind git\'s own global flags",
           'git -C /tmp/repo --no-pager commit -m "fix\n\nClaude-Session: x"')

    print("\nnon-Bash tools are none of its business:")
    denied, _ = run_hook({
        "agent_type": "builder", "tool_name": "Write",
        "tool_input": {"file_path": "msg.txt",
                       "content": "Co-Authored-By: Claude <noreply@anthropic.com>"}})
    check("a Write is not inspected (the commit that uses it will be)", denied, False)

    print("\nreads a message file the command string does not contain:")
    fd, path = tempfile.mkstemp(suffix=".txt", text=True)
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("fix the thing\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n")
        denies("git commit -F <file> whose file carries the trailer",
               'git commit -F "%s"' % path)
        denies("--file=<file> form", 'git commit --file=%s' % path)

        with open(path, "w", encoding="utf-8") as fh:
            fh.write("fix the thing\n\nreviewed by a human\n")
        allows("a clean message file", 'git commit -F "%s"' % path)
    finally:
        os.remove(path)

    allows("a -F pointing at a file that does not exist is not a crash",
           'git commit -F /nonexistent/path/to/msg.txt')

    print("\nfailure modes:")
    proc = subprocess.run([sys.executable, HOOK], input="not json at all",
                          capture_output=True, text=True)
    check("a malformed payload with no commit in it is ALLOWED",
          proc.stdout.strip(), "")
    check("a malformed payload still exits 0", proc.returncode, 0)

    proc = subprocess.run([sys.executable, HOOK],
                          input='{"tool_name": "Bash", broken git commit -m x',
                          capture_output=True, text=True)
    out = proc.stdout.strip()
    denied = names_itself = False
    if out:
        decision = json.loads(out)["hookSpecificOutput"]
        denied = decision.get("permissionDecision") == "deny"
        names_itself = "GUARD ITSELF IS BROKEN" in decision.get(
            "permissionDecisionReason", "")
    check("an unparseable payload that MENTIONS committing is denied", denied, True)
    check("and the denial names the guard, not the node", names_itself, True)
    check("a failing guard still exits 0", proc.returncode, 0)

    # The broken-hook path, driven the way the scope guard's test drives it: corrupt a
    # copy of the file rather than the file itself. Two injection points, because the
    # fallback in `main()` exists for the second one -- a guard whose `deny` is what
    # broke still has to deny, and cannot do it by calling `deny`.
    with open(HOOK, encoding="utf-8") as fh:
        source = fh.read()

    for label, anchor in (("the matcher", "def decide(raw):"),
                          ("`deny` itself", "def deny(reason):")):
        broken = HOOK + ".broken.py"
        with open(broken, "w", encoding="utf-8") as fh:
            fh.write(source.replace(
                anchor, anchor + "\n    raise RuntimeError('boom')", 1))
        try:
            proc = subprocess.run(
                [sys.executable, broken],
                input=json.dumps(bash('git commit -m "fix\n\nClaude-Session: x"')),
                capture_output=True, text=True)
            out = proc.stdout.strip()
            denied = names_itself = False
            if out:
                decision = json.loads(out)["hookSpecificOutput"]
                denied = decision.get("permissionDecision") == "deny"
                names_itself = "GUARD ITSELF IS BROKEN" in decision.get(
                    "permissionDecisionReason", "")
            check("a guard broken at %s DENIES rather than allowing" % label, denied, True)
            check("the denial from %s names the guard" % label, names_itself, True)
            check("a guard broken at %s still exits 0" % label, proc.returncode, 0)
        finally:
            os.remove(broken)

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
