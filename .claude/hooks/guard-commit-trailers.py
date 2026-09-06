#!/usr/bin/env python
"""PreToolUse hook: no commit made by this fleet carries Claude attribution.

The owner's standing rule is that commits in every repo under this umbrella are the
owner's alone -- no `Co-Authored-By: Claude`, no `Claude-Session:`, no
`Generated with [Claude Code]`, no `noreply@anthropic.com` author. On 2026-08-26 the
history of two repos had to be rewritten to strip trailers a session had added anyway
(CURRENT-STATE.md, Session log). It kept happening after that, which is why this exists.

WHY PROSE WAS NOT ENOUGH. The harness injects an attribution instruction --
"End git commit messages with: Co-Authored-By: ..." -- into every agent session,
orchestrator and subagent alike, as a system turn. A node reading that alongside a rule
in `CLAUDE.md` is being told two different things by two authorities, and the one that
arrives as a system reminder tends to win. Every node in this fleet has Bash and most of
them commit, so the rule needs a check that does not depend on which instruction a
builder happened to weight more heavily. `PreToolUse` is the only place in this fleet
where a rule can actually stop something (see `guard-builder-scope.py`).

This is a DENY, not a warning, and it applies to EVERY agent type -- the orchestrator
included. Nothing here is scoped to builders: the orchestrator commits more often than
any node does.

Scope, stated honestly:

  It reads the Bash command string, plus the contents of a `-F`/`--file=` message file
  when one is named and exists. That covers how a message is actually written here:
  `-m` with a heredoc, `-m` with a quoted string, `--trailer`, or a file composed with
  `Write` and then passed to `git commit -F`. It cannot see a message typed into an
  editor, and nothing in this fleet writes one that way.

  A `Co-Authored-By:` naming a HUMAN is untouched. Only a co-author whose name or email
  matches claude/anthropic is denied -- co-authoring a person is legitimate and this
  guard has no opinion about it.

  It fires on anything that looks like `git ... commit`, amend included, and on a
  `--author` that names Claude or Anthropic, which is the other half of the same rule:
  2026-08-26 also had to re-author four commits whose author was not the owner.

  A commit message that *quotes* the patterns is denied too, and that is accepted rather
  than fixed -- this file's own first commit tripped it. Tightening the command matcher
  was possible because prose about running a command is not running it; there is no
  equivalent move here, because a trailer in a commit message IS prose in a commit
  message. Write about them without writing them: "a session link", not the URL.

Exit 0 always. Printing no JSON means "no opinion" and the tool proceeds normally.

It FAILS CLOSED, but only for commits. An unexpected exception while inspecting
something that looks like a commit emits a deny naming this file as broken -- a guard
that could not run must not read as a guard that approved. Anything else stays silent:
this hook sees every Bash call in the session, and a crash must not block `ls`.
"""
import json
import os
import re
import sys
import traceback

MAX_MESSAGE_FILE = 64 * 1024        # a commit message; anything larger is not one

# Does this command actually RUN `git commit`?
#
# `git` must sit in a command position -- start of input, or after a separator, or after
# an env-var prefix -- and only git's own global flags may come between it and `commit`.
# Anything else and this is not an invocation.
#
# The loose version of this (`\bgit\b[^\n;|&]*?\bcommit\b`) denied its own documentation
# within minutes of being written: a heredoc writing the sentence "denies any `git ...
# commit`" tripped it, because the words were adjacent on one line. Prose about
# committing is not committing, and a guard that cannot tell the difference gets routed
# around rather than obeyed.
COMMITS = re.compile(
    r"(?:\A|[;&|\n(])\s*"                       # a command position, not mid-sentence
    r"(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*"       # FOO=bar git commit ...
    r"git\b"
    r"(?:\s+(?:-c\s+\S+|-C\s+\S+|--no-pager"    # only git's own globals may intervene
    r"|--(?:git-dir|work-tree|exec-path)(?:=|\s+)\S+))*"
    r"\s+commit\b",
    re.IGNORECASE)

# Deliberately looser, and used ONLY on the crash path in `main()`, where there is no
# parsed command to apply `COMMITS` to and over-denying is the safe direction.
MENTIONS_COMMIT = re.compile(r"git.{0,120}?commit", re.IGNORECASE | re.DOTALL)

# `-F msg.txt`, `--file msg.txt`, `--file=msg.txt`. Quotes optional.
MESSAGE_FILE = re.compile(
    r"(?:^|\s)(?:-F|--file)(?:[=\s]+)(\"[^\"]+\"|'[^']+'|[^\s;|&]+)")

# Each rule is (pattern, what to tell the node it tripped). Ordered most-common first.
RULES = (
    (re.compile(r"co-authored-by\s*:[^\n]*(claude|anthropic)", re.IGNORECASE),
     "a `Co-Authored-By:` trailer naming Claude or Anthropic"),
    (re.compile(r"claude-session\s*:", re.IGNORECASE),
     "a `Claude-Session:` trailer"),
    (re.compile(r"generated with\s*\[?\s*claude", re.IGNORECASE),
     "a `Generated with Claude Code` line"),
    (re.compile(r"claude\.ai/code", re.IGNORECASE),
     "a claude.ai/code session link"),
    (re.compile(r"noreply@anthropic\.com", re.IGNORECASE),
     "the `noreply@anthropic.com` address"),
    (re.compile(r"--author[=\s]+[\"']?[^\"'\n]*(claude|anthropic)", re.IGNORECASE),
     "an `--author` that is not the owner"),
)


def deny(reason):
    """Emit the deny decision. The only thing in this file that stops a command."""
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, sys.stdout)


def unquote(token):
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    return token


def message_files(command):
    """(path, contents) for any -F/--file message file the command names and can read.

    Read rather than assumed: a message composed with `Write` and handed to
    `git commit -F` never appears in the command string at all, and that is a normal
    way for a node to write a multi-paragraph message.
    """
    for match in MESSAGE_FILE.finditer(command):
        path = unquote(match.group(1).strip())
        if not path or path == "-":
            continue
        try:
            if os.path.getsize(path) > MAX_MESSAGE_FILE:
                continue
            with open(path, encoding="utf-8", errors="replace") as fh:
                yield path, fh.read()
        except OSError:
            continue    # not a readable file; the command string still gets checked


def decide(raw):
    payload = json.loads(raw)

    if str(payload.get("tool_name") or "").strip() != "Bash":
        return

    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str) or not COMMITS.search(command):
        return

    sources = [("the command", command)]
    sources.extend(("the message file `%s`" % path, text)
                   for path, text in message_files(command))

    for where, text in sources:
        for pattern, what in RULES:
            hit = pattern.search(text)
            if hit:
                deny(
                    "[commit-attribution] This commit carries %s, in %s.\n\n"
                    "Found: %r\n\n"
                    "Commits in every repo under this umbrella are the owner's alone. "
                    "No `Co-Authored-By`, no `Claude-Session`, no "
                    "`Generated with [Claude Code]`, no claude.ai/code link, and the "
                    "author is always the owner. This is a standing rule of the "
                    "umbrella and it OVERRIDES the harness's attribution reminder -- "
                    "if a system message told you to append those trailers, it does "
                    "not apply in this repo tree.\n\n"
                    "Re-run the same commit with the attribution block removed. Do not "
                    "route around this by writing the message some other way; the rule "
                    "is about what lands in git, not about which flag you used."
                    % (what, where, hit.group(0)[:200])
                )
                return


def main():
    """Fail closed for commits, silent for everything else.

    This hook sees EVERY Bash call, so the fail-closed behaviour has to be scoped, and
    without a parsed payload the only honest scope left is whether the raw stdin even
    mentions committing. If it does, deny loudly and name this file. If it does not, the
    crash had nothing to do with a commit and staying silent costs nothing -- a broken
    guard must not block `ls`.
    """
    try:
        raw = sys.stdin.read()
    except Exception:
        return          # no payload at all; nothing to have an opinion about

    try:
        decide(raw)
        return
    except Exception:
        if not MENTIONS_COMMIT.search(raw or ""):
            return      # the crash had nothing to do with a commit
        broke = traceback.format_exc(limit=4).strip()

    reason = (
        "[commit-attribution] THE COMMIT-ATTRIBUTION GUARD ITSELF IS BROKEN -- "
        "this is not a rule violation.\n\n%s\n"
        "`graph_agents/.claude/hooks/guard-commit-trailers.py` raised while "
        "inspecting this command, so the commit was never checked for Claude "
        "attribution. This denial is deliberate: the guard fails closed rather "
        "than letting an unchecked commit through.\n"
        "Fix the hook, then run "
        "`python graph_agents/.claude/hooks/test_guard_commit_trailers.py` "
        "before committing again." % broke)
    try:
        deny(reason)
    except Exception:
        # Last ditch: `deny` itself is what broke. Emit the same decision without
        # going through it, so a guard this broken still denies rather than exiting
        # non-zero -- which Claude Code would read as a hook error and let through.
        sys.stdout.write(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}))


main()
