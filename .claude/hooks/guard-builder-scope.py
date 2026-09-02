#!/usr/bin/env python
"""PreToolUse hook: a builder may not write outside the file set the human approved.

The gate in `feature-graph` step 4 shows a human a plan whose slices name specific
files, and the human approves *that*. Until now nothing checked it afterwards -- a
builder could edit anything in the target and the approval meant only that the run was
allowed to start. This makes the approved file set a boundary instead of a description.

DENIES rather than warns. A warning after the write has already happened is a record of
the violation, not a guard against it, and `PreToolUse` is the only place in this fleet
where a rule can actually stop something.

Scope, stated honestly:

  It compares against the UNION of every slice's `files`, not the acting builder's own
  slice. A hook is given `agent_id`, never a slice id, and nothing maps one to the other.
  In `single-loop` -- which is every run this fleet has executed -- the union IS the one
  slice, so the guard is exact. In a diamond, worktrees already keep builders out of each
  other's trees, so what the union still buys is the plan boundary itself.

  It matches a builder working in a linked git WORKTREE by repo-relative path, since a
  worktree's absolute paths are rooted outside the umbrella and can never equal the
  plan's. The repo is taken to be a plan entry's first path segment, which holds because
  every node under the umbrella owns its own repo. If that ever stops being true the
  entry fails to match and only the absolute rule applies -- the guard narrows, never
  widens.

  It fires only for `agent_type == "builder"`. The orchestrator is not constrained here:
  it is not supposed to be implementing at all, and `feature-graph` says so in words.

  It is silent when there is no open run, when the run is closed, when the plan lists no
  files, and when `approved_by_human` is not yet true -- in that last case a builder
  should not be running, but that is `--audit`'s finding to report, and denying every
  write instead would deadlock a run whose approval simply has not been recorded yet.

The escape hatch is `scope_exceptions` in the run's `state.json`, which the orchestrator
owns. Adding a path there is deliberate and auditable; editing `architect.plan` to widen
the file set would be the orchestrator rewriting another node's key, which is exactly
what `written_by` was added to catch.

Exit 0 always. Printing no JSON means "no opinion" and the tool proceeds normally.
"""
import fnmatch
import json
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
FLEET = os.path.normpath(os.path.join(HERE, "..", ".."))      # graph_agents/
UMBRELLA = os.path.dirname(FLEET)                             # repos/
CURRENT = os.path.join(FLEET, ".graph", "CURRENT")
CLOSED = ("done", "blocked")


def norm(path):
    """Absolute, junction-resolved, forward-slashed, case-folded on Windows."""
    try:
        real = os.path.realpath(path)
    except Exception:
        real = path
    real = str(real).replace("\\", "/").rstrip("/")
    return real.lower() if os.name == "nt" else real


def open_run():
    """(state, run_dir) for the run `.graph/CURRENT` points at, or (None, None)."""
    try:
        with open(CURRENT, encoding="utf-8") as fh:
            run_id = fh.read().strip()
    except OSError:
        return None, None
    if not run_id:
        return None, None
    run_dir = os.path.join(FLEET, ".graph", "runs", run_id)
    try:
        with open(os.path.join(run_dir, "state.json"), encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        return None, None
    return (state, run_dir) if isinstance(state, dict) else (None, None)


def approved_paths(state, run_dir):
    """{normalised path: as the plan wrote it}. The key compares, the value is read.

    Comparison is case-folded on Windows and the display is not, so the denial message
    quotes the plan's own spelling back rather than a lowercased path the human never
    typed.
    """
    allowed = {norm(os.path.join(run_dir, "state.json")):    # nodes must write their key
               "%s/state.json" % os.path.basename(run_dir)}
    rel_map = {}

    plan = (state.get("architect") or {}).get("plan")
    entries = []
    if isinstance(plan, list):
        for slice_ in plan:
            if isinstance(slice_, dict) and isinstance(slice_.get("files"), list):
                entries.extend(f for f in slice_["files"] if isinstance(f, str))

    exceptions = state.get("scope_exceptions")
    if isinstance(exceptions, list):
        entries.extend(f for f in exceptions if isinstance(f, str))

    planned = False
    for entry in entries:
        entry = entry.strip()
        # A plan whose `files` still reads like prose is not a file set. Anything with a
        # space and no separator is a description, and treating it as a path would let
        # the union match nothing and deny everything.
        if not entry or (" " in entry and "/" not in entry and "\\" not in entry):
            continue

        # A plan entry is a GLOB, not a literal path: an architect writes
        # `huntstack/apps/mobile/**` to mean "everything under apps/mobile". Reduce a
        # trailing wildcard segment to the directory it stands for, so the prefix tests
        # below cover it.
        #
        # Without this the normalised entry kept its literal `**`, and since no real file
        # is ever equal to -- or prefixed by -- a path ending in `**`, the guard denied
        # EVERY write under an approved directory. That happened on 2026-09-01: three
        # slices of `2026-09-01-huntstack-mobile` had `huntstack/apps/mobile/**` as their
        # entire file set, and s1's builder could not create so much as a package.json in
        # a directory the human had explicitly approved. It cost a round trip and a
        # `scope_exceptions` entry that granted nothing the plan had not already granted.
        #
        # This narrows nothing: under the prefix rule `a/b/**` and `a/b` cover exactly the
        # same files. Residual wildcards deeper in the entry (`a/**/*.ts`) survive here and
        # are matched by fnmatch in `_match` instead.
        entry_path = entry.replace("\\", "/").rstrip("/")
        while True:
            head, _, tail = entry_path.rpartition("/")
            if head and tail in ("**", "*"):
                entry_path = head
                continue
            break
        if not entry_path:
            continue

        allowed[norm(entry_path if os.path.isabs(entry_path)
                     else os.path.join(UMBRELLA, entry_path))] = entry

        # Same entry, expressed as (repo root, path within that repo). A plan entry's
        # first segment IS the repo, because every node under the umbrella owns its own
        # repo -- see CLAUDE.md. This is what lets a builder in a linked worktree be
        # matched: same repo-relative path, different root. If the assumption is ever
        # wrong the entry simply fails to match here and the absolute rule above still
        # applies, so the guard degrades to its previous behaviour rather than opening up.
        parts = entry_path.strip("/").split("/")
        if len(parts) >= 2 and not os.path.isabs(entry_path):
            root = norm(os.path.join(UMBRELLA, parts[0]))
            rel = "/".join(parts[1:])
            rel_map.setdefault(root, {})[rel.lower() if os.name == "nt" else rel] = entry

        planned = True

    return (allowed, rel_map) if planned else (None, None)


def _match(target, approved):
    """One approved entry against one target path.

    Exact hit, or living under an approved directory, or -- when the entry still carries
    a wildcard after `approved_paths` reduced its trailing one -- an fnmatch. Both call
    sites go through here on purpose: the absolute rule and the worktree rule drifted
    apart once already, and a matcher that lives in two places is a matcher that will
    disagree with itself.
    """
    if target == approved or target.startswith(approved + "/"):
        return True
    if "*" in approved or "?" in approved:
        return fnmatch.fnmatch(target, approved)
    return False


def covered(target, allowed):
    """True if the target is an approved path, or lives under an approved directory."""
    return any(_match(target, a) for a in allowed)


def worktree_context(target):
    """(main repo root, path relative to the worktree root), or (None, None).

    A linked git worktree has a `.git` FILE (not a directory) reading
    `gitdir: <main>/.git/worktrees/<name>`. That is read directly rather than shelling
    out to git: this is a PreToolUse hook, it runs before EVERY write, and it must not
    pay for a subprocess on the hot path.

    Returns (None, None) for a main working tree -- there `.git` is a directory and the
    absolute rule in approved_paths already covers the path correctly.
    """
    directory = os.path.dirname(target)
    for _ in range(64):                      # bounded: never walk forever on a odd path
        dotgit = os.path.join(directory, ".git")
        if os.path.isdir(dotgit):
            return None, None                # main tree; absolute rule handles it
        if os.path.isfile(dotgit):
            try:
                with open(dotgit, encoding="utf-8") as fh:
                    line = fh.read().strip()
            except OSError:
                return None, None
            if not line.startswith("gitdir:"):
                return None, None
            gitdir = norm(line.split(":", 1)[1].strip())
            marker = "/.git/worktrees/"
            if marker not in gitdir:
                return None, None
            root = norm(directory)
            if target != root and not target.startswith(root + "/"):
                return None, None
            return gitdir.split(marker)[0], target[len(root) + 1:]
        parent = os.path.dirname(directory)
        if parent == directory:
            return None, None
        directory = parent
    return None, None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    if str(payload.get("agent_type") or "").strip() != "builder":
        return

    path = (payload.get("tool_input") or {}).get("file_path")
    if not path:
        return

    state, run_dir = open_run()
    if state is None:
        return
    if str(state.get("status") or "").strip().lower() in CLOSED:
        return          # a stale pointer must not constrain the next run's builder
    if state.get("approved_by_human") is not True:
        return          # --audit owns that finding; denying here would deadlock the run

    allowed, rel_map = approved_paths(state, run_dir)
    if allowed is None:
        return          # no file set to compare against

    target = norm(path)
    if covered(target, allowed):
        return

    # Diamond mode: the builder is in a linked worktree, so its absolute path is rooted
    # somewhere else entirely and can never equal the plan's umbrella-relative path. Match
    # the repo-relative path against the same repo's approved entries instead. Without
    # this the guard denies EVERY write by EVERY builder in a diamond -- which it did,
    # undetected, from the day it was written until the first run actually fanned out.
    main_root, rel = worktree_context(target)
    if main_root and rel:
        entries = rel_map.get(main_root) or {}
        if any(_match(rel, a) for a in entries):
            return

    listed = "\n".join("  - %s" % shown for shown in sorted(allowed.values()))
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "[plan-scope] `%s` is not in the file set a human approved for run `%s`.\n"
                "Approved:\n%s\n"
                "Do not work around this. Stop, report to the orchestrator what you need "
                "and why the approved set was wrong, and let it decide: either the work "
                "belongs to a different slice, or the orchestrator records the extension "
                "in `scope_exceptions` and in this slice's `deviation_from_approved_plan`. "
                "Silently widening scope after the gate is the failure the gate exists to "
                "prevent." % (path, os.path.basename(run_dir), listed)
            ),
        }
    }, sys.stdout)


main()
