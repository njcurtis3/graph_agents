#!/usr/bin/env python
"""PostToolUse hook: flag a cross-app import the moment it is written.

The umbrella's one invariant -- no app imports, builds against, or reads files from
another app -- was prose only. `graph_agents/.graph/verify-invariant.py` made it
checkable; this makes it checkable *at the moment of the edit*, instead of whenever
someone remembers to run the checker.

Flag only, never block. Exit 0 always, even on a violation: the fix belongs to the agent
that made the edit, and a hook that fails a legitimate write is worse than a missed one.

The rule itself is NOT reimplemented here. `check_file()` is imported from the checker so
there is exactly one definition of what counts as a violation; if the two ever disagreed,
the pre-commit answer and the live answer would differ and neither would be trustworthy.

`repos/.claude` is a directory junction into `graph_agents/.claude`, so both this file and
the file being edited have two valid absolute paths. Everything is resolved through
`os.path.realpath()` before it is compared -- same reason the staleness hook does.
"""
import importlib.util, json, os, sys

# The checker's filename is hyphenated, so it is not importable by name. Load it by
# path, from the fleet root this hook resolves to through the junction.
HOOKS = os.path.dirname(os.path.realpath(__file__))
CHECKER = os.path.join(os.path.dirname(os.path.dirname(HOOKS)), ".graph",
                       "verify-invariant.py")


def _load_checker():
    """The checker module, or None. A broken checker must not break the edit."""
    try:
        spec = importlib.util.spec_from_file_location("verify_invariant", CHECKER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


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

    checker = _load_checker()
    if checker is None:
        return

    try:
        # An unreadable registry raises SystemExit(2) in the checker. That is right for a
        # command and wrong for a hook, so it is swallowed here along with everything else.
        apps = checker.load_registry()
        boundaries = apps + [("graph_agents", checker.resolve(checker.FLEET))]
        violations = checker.check_file(path, boundaries)
    except (Exception, SystemExit):
        return

    # check_file() is already silent for non-source files and for anything outside a
    # registered app -- which is the fleet's own tooling, and every doc and config file.
    if not violations:
        return

    message = (
        "[cross-app] You just wrote a cross-app import. The umbrella's one invariant is "
        "that no app may import, build against, or read files from another app:\n"
        + "\n".join("  " + v for v in violations) + "\n"
        "Before this turn ends: remove the edge. If both apps need the same thing, copy "
        "it into this app and let the two copies drift -- `copy, don't couple`. Do not "
        "introduce a shared package, and do not widen the import to reach the same file "
        "another way."
    )

    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": message,
        }
    }, sys.stdout)


main()
